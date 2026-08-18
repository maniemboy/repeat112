# -*- coding: utf-8 -*-
"""
리핏112 (RE:PEAT 112) — 오프라인 AI 어시스턴트 모듈
================================================================
외부 API·인터넷 연결 없이 동작한다. 1차 버전은 거대 LLM이 아니라
'키워드·정규식 기반 의도 파악 + 구조화된 태그 저장'으로 구현했다.

두 가지 역할
  1) 질의응답: analysis.py가 만든 결과(트랙·순찰추천·재발가속 등)를 자연어 질문에
     맞춰 찾아서 답한다. (answer_query)
  2) 현장지식 학습: "BASE00006은 구미차병원이야. 시설거점-병원으로 기억해." 같은
     문장에서 장소코드·태그·시설유형을 추출해 '저장 후보'를 만든다. 이 모듈은
     저장을 직접 실행하지 않는다 — 후보만 반환하고, 실제 저장(analysis.upsert_tag)
     은 반드시 화면에서 사용자가 확인 버튼을 눌러야 실행된다. (parse_teach)

확장 지점
  아래 RuleBasedEngine과 동일한 인터페이스(parse_teach, answer_query)를 구현하는
  클래스를 만들면(예: 내부망 로컬 LLM 연동 LocalLLMEngine), app.py의 엔진 교체
  한 줄로 바꿔치기할 수 있다. 이 모듈은 pandas 외 외부 통신 라이브러리를 쓰지
  않는다 — 로컬 LLM으로 확장하더라도 외부 API 호출 없이 로컬 추론만 써야 한다.
"""

from __future__ import annotations

import re

import pandas as pd

from analysis import COL_BASE, TAG_OPTIONS, FACILITY_SUBTYPES

BASE_ID_PATTERN = re.compile(r"base\s*0*([0-9]{2,6})", re.IGNORECASE)

TAG_KEYWORDS = {
    "시설거점": ["시설거점", "시설 거점", "시설이야", "시설임"],
    "행정접수 거점": ["행정접수 거점", "행정접수", "행정 거점", "접수창구"],
    "실제 반복지점": ["실제 반복지점", "반복지점", "진짜 반복", "진짜반복", "진짜 위험"],
    "확인 안 됨": ["확인 안 됨", "미확인으로", "모르겠어", "아직 몰라"],
}
FACILITY_KEYWORDS = {
    "병원": ["병원", "의료원", "메디컬센터", "응급실"],
    "숙박시설": ["숙박", "모텔", "호텔", "여관", "게스트하우스"],
    "복지시설": ["복지", "요양원", "요양시설", "보호시설", "복지센터"],
}

HELP_TEXT = (
    "이렇게 물어보실 수 있어요:\n"
    "- '오늘 야간 우선순찰 장소 알려줘'\n"
    "- '최근 가정폭력 재발가속 지점은?'\n"
    "- '왜 BASE00037이 순찰에서 제외됐어?'\n"
    "- '시설의심 후보 알려줘'\n"
    "- 'BASE00006은 구미차병원이야. 시설거점-병원으로 기억해.'"
)


# ═══════════════════════════════════════════════════════
# 장소코드·태그 추출
# ═══════════════════════════════════════════════════════
def extract_base_ids(text: str, known_ids: set[str] | None = None) -> list[str]:
    """본문에서 BASE 장소코드를 뽑는다. 알려진 코드 집합이 있으면 그중 일치하는
    코드를 우선하고(자릿수 표기가 달라도 매칭), 없으면 그냥 정규화한 후보를 준다."""
    raw = [m.group(1) for m in BASE_ID_PATTERN.finditer(text)]
    if not raw:
        return []
    candidates = []
    for num in raw:
        n = int(num)
        candidates.append(f"BASE{n:05d}")
        candidates.append(f"BASE{n:04d}")
        candidates.append(f"BASE{n:03d}")
    if known_ids:
        matched = [c for c in candidates if c in known_ids]
        if matched:
            # 중복 제거, 순서 유지
            seen = []
            for m in matched:
                if m not in seen:
                    seen.append(m)
            return seen
    # known_ids와 못 맞추면 5자리 표기를 기본값으로
    return [f"BASE{int(num):05d}" for num in raw]


def parse_teach(text: str, known_ids: set[str] | None = None) -> dict | None:
    """
    현장지식 학습 의도를 감지한다. 장소코드와 태그 키워드가 모두 있어야
    '학습 후보'로 인정한다(둘 다 없으면 질의응답으로 넘어간다).
    반환값은 저장 후보 dict 또는 None. 이 함수는 절대 저장을 실행하지 않는다.
    """
    base_ids = extract_base_ids(text, known_ids)
    if not base_ids:
        return None

    tag = None
    for t, kws in TAG_KEYWORDS.items():
        if any(k in text for k in kws):
            tag = t
            break

    facility_type = None
    if tag in (None, "시설거점"):
        for sub, kws in FACILITY_KEYWORDS.items():
            if any(k in text for k in kws):
                facility_type = sub
                if tag is None:
                    tag = "시설거점"  # 시설명이 언급되면 시설거점으로 추정
                break

    if tag is None:
        return None
    if tag == "시설거점" and facility_type is None:
        facility_type = "기타"

    return {
        "base_id": base_ids[0], "tag": tag, "facility_type": facility_type,
        "raw_text": text.strip(),
    }


# ═══════════════════════════════════════════════════════
# 질의응답
# ═══════════════════════════════════════════════════════
def answer_query(text: str, ctx: dict) -> str | None:
    """
    ctx = {"tracks":..., "patrol":..., "accel":..., "facility_suspects":...}
    (모두 analysis.py 결과 DataFrame, app.py에서 매 rerun마다 만들어 넘겨준다)
    이해하지 못하면 None을 반환한다(호출부에서 HELP_TEXT로 대체).
    """
    tracks = ctx.get("tracks", pd.DataFrame())
    patrol = ctx.get("patrol", pd.DataFrame())
    accel = ctx.get("accel", pd.DataFrame())
    facility_suspects = ctx.get("facility_suspects", pd.DataFrame())
    t = text.strip()

    # 1) "왜 OOO 제외됐어?" — 특정 장소 판정 설명
    if ("왜" in t or "이유" in t or "사유" in t) and len(tracks):
        ids = extract_base_ids(t, set(tracks[COL_BASE]))
        if ids:
            bid = ids[0]
            row = tracks[tracks[COL_BASE] == bid]
            if len(row):
                r = row.iloc[0]
                return (f"{bid} → 트랙 '{r['트랙']}'\n"
                       f"판정사유: {r['판정사유']}\n원천: {r['원천']}\n"
                       f"건수 {int(r['건수'])} · 주요유형 {r['주요유형']}")
            return f"{bid}에 대한 데이터를 찾지 못했습니다."
        return "장소코드를 못 찾았어요. 'BASE00037은 왜 제외됐어?'처럼 코드를 포함해 물어봐주세요."

    # 2) 재발가속 지점
    if "재발가속" in t or ("가속" in t and "지점" in t):
        sub = tracks[tracks["판정사유"].astype(str).str.contains("재발가속", na=False)] if len(tracks) else pd.DataFrame()
        if len(sub) == 0:
            return "현재 재발가속으로 확인된 지점이 없습니다."
        lines = [f"- {r[COL_BASE]} ({r['주요유형']}, {int(r['건수'])}건)"
                for _, r in sub.head(5).iterrows()]
        return "재발가속 지점:\n" + "\n".join(lines)

    # 3) 시설의심 후보
    if "시설의심" in t or ("시설" in t and ("후보" in t or "의심" in t)):
        if len(facility_suspects) == 0:
            return "현재 시설의심 후보가 없습니다."
        lines = [f"- {r[COL_BASE]} ({r['사유']})" for _, r in facility_suspects.head(5).iterrows()]
        return "시설의심 후보 (확인 필요):\n" + "\n".join(lines)

    # 4) 확인대기 목록
    if "확인대기" in t or "확인 대기" in t:
        sub = tracks[tracks["트랙"] == "확인대기"] if len(tracks) else pd.DataFrame()
        if len(sub) == 0:
            return "현재 확인대기 지점이 없습니다."
        lines = [f"- {r[COL_BASE]} ({r['판정사유']})" for _, r in sub.head(5).iterrows()]
        return f"확인대기 지점 {len(sub)}곳 중 상위:\n" + "\n".join(lines)

    # 5) 우선순찰 (시간대·유형 필터)
    if "순찰" in t:
        sub = patrol.copy() if len(patrol) else pd.DataFrame()
        if len(sub) == 0:
            return "현재 맞춤형 순찰 추천 지점이 없습니다."
        if "야간" in t:
            sub = sub[sub["추천순찰시간대"] == "야간"]
        elif "주간" in t:
            sub = sub[sub["추천순찰시간대"] == "주간"]
        elif "저녁" in t:
            sub = sub[sub["추천순찰시간대"] == "저녁"]
        for ty in sub["주요유형"].unique().tolist():
            if isinstance(ty, str) and ty in t:
                sub = sub[sub["주요유형"] == ty]
                break
        if len(sub) == 0:
            return "조건에 맞는 순찰 추천 지점이 없습니다."
        lines = [f"- {r[COL_BASE]} ({r['주요유형']}, {r['추천순찰시간대']}) → {r['추천행동']}"
                for _, r in sub.head(5).iterrows()]
        return "우선 순찰 추천:\n" + "\n".join(lines)

    return None


# ═══════════════════════════════════════════════════════
# 엔진 인터페이스 (확장 지점)
# ═══════════════════════════════════════════════════════
class RuleBasedEngine:
    """1차 버전: 키워드·정규식 기반. 아래 두 메서드 시그니처를 유지하는
    엔진이라면 app.py에서 바꿔치기만 하면 된다."""

    def parse_teach(self, text: str, known_ids: set[str] | None = None) -> dict | None:
        return parse_teach(text, known_ids)

    def answer_query(self, text: str, ctx: dict) -> str | None:
        return answer_query(text, ctx)


# 향후 확장 예시 (주석):
# class LocalLLMEngine:
#     """내부망 로컬 LLM(예: llama.cpp, 로컬 추론 서버) 연동용. 외부 API 호출
#     없이 로컬 모델 파일/프로세스만 사용해야 한다는 원칙은 그대로 유지한다."""
#     def __init__(self, model_path): ...
#     def parse_teach(self, text, known_ids=None): ...
#     def answer_query(self, text, ctx): ...

DEFAULT_ENGINE = RuleBasedEngine()
