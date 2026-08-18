# -*- coding: utf-8 -*-
"""
리핏112 (RE:PEAT 112) — 핵심 분석 모듈 v2
================================================================
실제 업무데이터 스키마(Repeat112_PowerFew_분석용_v3.xlsx '분석데이터' 시트)를
그대로 입력으로 받는다. 개인정보·자유서술문은 이 데이터에 애초에 없다.

파이프라인
  1. clean()                 데이터 정제 (코드 표기 통일 등)
  2. concentration()         Power Few 집중도 (상위 1/5/10%, 로렌츠, 지니)
  3. detect_admin_artifacts()행정접수 거점 자동 판별 (유형게이트+SITE 집중도, 2단계)
  4. detect_institutional_surge()  제도변화형 급증 '의심 후보' 탐지 (자동제외 아님)
  5. detect_acceleration()   재발가속 장소 탐지 (최근 간격 vs 과거 간격)
  6. detect_facility_suspects()  시설집중 거점 '의심 후보' 탐지 (자동제외 아님)
  6-c. load_tags/save_tags/upsert_tag  거점 태그 저장소 (로컬 JSON, 재실행 후에도 유지)
  6-d. classify_tracks()     AI 후보제시 → 경찰관 확인 → 태그 반영까지 결합한 최종 트랙 판정
  7. recommend_patrol()      '맞춤형 순찰' 트랙만 대상으로 시간대 결합 추천
  8. build_top3()            순찰추천 + 인계메모 → 교대 브리핑 TOP3 (사람 긴급메모 최우선)
  9. split_validation()      시간분할 검증 (월 순서 기준 전반기/후반기)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

COL_BASE = "LOC_BASE_ID"
COL_SITE = "LOC_SITE_ID"
COL_TYPE = "사건종별"
COL_CAT = "종별분류"
COL_CODE = "코드"
COL_YEAR = "연도"
COL_MONTH = "월"
COL_MSEQ = "월순번"
COL_GAP_BASE = "BASE_직전신고간격_일"
COL_DONG = "행정동"

REQUIRED_COLS = [COL_BASE, COL_TYPE, COL_YEAR, COL_MONTH]

# 코드 표기 정규화 (예: 'C1선' → 'C1')
CODE_FIX = {"C1선": "C1", "c1": "C1", "c2": "C2", "c3": "C3", "c4": "C4", "c0": "C0"}
HIGH_RISK_CODES = {"C0", "C1"}

INTERVENTION_MAP = {
    "가정폭력": "피해자 보호형 (여청 기능·보호시설 연계)",
    "스토킹": "피해자 보호형 (잠정조치·보호수단 검토)",
    "스토킹 전자장치": "제도관리형 (전자감독 기기 이력, 개별 위험판단 아님)",
    "성폭력": "피해자 보호형 (여청 기능 연계)",
    "행패소란": "순찰 강화형",
    "시비": "순찰·중재형",
    "절도": "순찰 강화형 (시간대 집중)",
    "폭행": "순찰 강화형",
    "변사자": "복지연계형 (고독사·고령가구 위험 검토)",
}
DEFAULT_INTERVENTION = "모니터링형 (반복 지속 시 재분류)"


# ═══════════════════════════════════════════════════════
# 1. 정제
# ═══════════════════════════════════════════════════════
def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    log = {}
    out = df.copy()

    before_dup = len(out)
    out = out.drop_duplicates()
    log["removed_duplicates"] = before_dup - len(out)

    if COL_CODE in out.columns:
        n_fixed = out[COL_CODE].isin(CODE_FIX).sum()
        out[COL_CODE] = out[COL_CODE].replace(CODE_FIX)
        log["normalized_codes"] = int(n_fixed)

    before_loc = len(out)
    out = out.dropna(subset=[COL_BASE])
    log["removed_no_location"] = before_loc - len(out)

    # 정렬용 시계열 키: 연도·월·월순번 (정확한 날짜 대신 순서 기반)
    out = out.sort_values([COL_YEAR, COL_MONTH, COL_MSEQ]).reset_index(drop=True)
    out["_MSEQ_KEY"] = (
        (out[COL_YEAR] - out[COL_YEAR].min()) * 12 + out[COL_MONTH]
    ) * 1000 + out[COL_MSEQ].fillna(0)

    log["final_rows"] = len(out)
    return out, log


def diagnose(df: pd.DataFrame) -> dict:
    report = {"missing_columns": [c for c in REQUIRED_COLS if c not in df.columns]}
    if report["missing_columns"]:
        return report
    report["total_rows"] = len(df)
    report["null_counts"] = df.isna().sum().to_dict()
    report["duplicate_rows"] = int(df.duplicated().sum())
    if COL_CODE in df.columns:
        report["code_anomalies"] = int(df[COL_CODE].isin(CODE_FIX).sum())
    return report


# ═══════════════════════════════════════════════════════
# 2. Power Few 집중도
# ═══════════════════════════════════════════════════════
def concentration(df: pd.DataFrame, exclude_types: list[str] | None = None) -> dict:
    d = df if not exclude_types else df[~df[COL_TYPE].isin(exclude_types)]
    counts = d.groupby(COL_BASE).size().sort_values(ascending=False)
    total = int(counts.sum())
    n = len(counts)
    result = {"n_places": n, "total_calls": total, "excluded_types": exclude_types or []}

    for pct in (1, 5, 10):
        k = max(1, int(np.ceil(n * pct / 100)))
        share = counts.iloc[:k].sum() / total if total else 0
        result[f"top{pct}"] = {"k_places": k, "share": float(share)}

    cum = np.cumsum(counts.values) / total if total else np.array([])
    x = np.arange(1, n + 1) / n if n else np.array([])
    lorenz_x = np.concatenate([[0.0], x])
    lorenz_y = np.concatenate([[0.0], cum])
    result["lorenz_x"], result["lorenz_y"] = lorenz_x.tolist(), lorenz_y.tolist()
    result["gini"] = float(2 * np.trapezoid(lorenz_y, lorenz_x) - 1) if n > 1 else 0.0
    result["top_places"] = counts
    return result


# 행정접수 처리 과정에서 창구 주소로 좌표가 몰릴 수 있는 유형(예시 목록).
# ⚠ 관할 실무 특성에 따라 조정이 필요하다 — 실제 접수·처리 관행을 아는
#   현장 인원이 최종 검토해야 하는 리스트다. 여기 없는 유형(가정폭력·스토킹·
#   주취자 등 특정 주소에 결부되는 행동기반 신고)은 SITE 집중도가 높아도
#   '진짜 반복지점'일 수 있으므로 아티팩트 판별 대상에서 원천적으로 제외한다.
ADMIN_PRONE_TYPES = ["분실습득", "변사자", "상담문의", "내용확인불가", "서비스요청"]


# ═══════════════════════════════════════════════════════
# 3. 행정접수 아티팩트 자동 판별 (2단계: 유형 게이트 + SITE 집중도)
# ═══════════════════════════════════════════════════════
def detect_admin_artifacts(df: pd.DataFrame,
                           admin_prone_types: list[str] | None = None,
                           site_share_threshold: float = 0.85,
                           min_count: int = 20) -> pd.DataFrame:
    """
    2단계 판별:
      1단계(유형 게이트) — 사건종별이 admin_prone_types(행정접수 처리 관행이
          있다고 알려진 유형)에 해당하는 건만 검토 대상으로 삼는다.
          가정폭력·스토킹처럼 특정 주소에 결부되는 행동기반 신고는 SITE
          집중도가 100%여도 '진짜 반복'이므로 애초에 검토하지 않는다.
      2단계(SITE 집중도) — 1단계를 통과한 (BASE,유형) 조합 중, 상위 1개
          SITE_ID 비중이 site_share_threshold 이상이면 '행정접수 아티팩트'.
    """
    admin_prone_types = admin_prone_types if admin_prone_types is not None else ADMIN_PRONE_TYPES
    if COL_SITE not in df.columns:
        return pd.DataFrame(columns=[COL_BASE, COL_TYPE, "건수", "최다SITE비중", "판정"])

    gated = df[df[COL_TYPE].isin(admin_prone_types)].dropna(subset=[COL_SITE])
    rows = []
    for (base, ctype), g in gated.groupby([COL_BASE, COL_TYPE]):
        if len(g) < min_count:
            continue
        top_site_share = g[COL_SITE].value_counts(normalize=True).iloc[0]
        if top_site_share >= site_share_threshold:
            rows.append({
                COL_BASE: base, COL_TYPE: ctype, "건수": len(g),
                "최다SITE비중": round(float(top_site_share), 3),
                "판정": "행정접수 아티팩트",
            })
    return pd.DataFrame(rows).sort_values("건수", ascending=False) if rows else pd.DataFrame(
        columns=[COL_BASE, COL_TYPE, "건수", "최다SITE비중", "판정"])


# ═══════════════════════════════════════════════════════
# 4. 제도변화형 급증 탐지
# ═══════════════════════════════════════════════════════
def detect_institutional_surge(df: pd.DataFrame, min_recent_share: float = 0.15,
                               max_baseline_share: float = 0.02) -> pd.DataFrame:
    """
    ⚠ 이 함수는 '의심 후보'만 찾아낸다. 실제로 분석에서 제외할지는 자동으로
    결정하지 않는다 — 사람이 확인한 뒤 apply_corrections()에 명시적으로
    넘긴 유형만 실제 제외된다 ('의심 → 확인 → 제외' 3단계 구조).

    사건종별별 월간 비중을 계산해, 과거엔 거의 없다가(<=max_baseline_share)
    최근엔 크게 늘어난(>=min_recent_share) 유형을 '의심 후보'로 표시한다.
    유형이 아예 등장하지 않은 달도 0건으로 채워 베이스라인을 왜곡 없이 계산한다.
    """
    all_months = (
        df[[COL_YEAR, COL_MONTH]].drop_duplicates().sort_values([COL_YEAR, COL_MONTH])
    )
    monthly_total = df.groupby([COL_YEAR, COL_MONTH]).size().rename("전체")

    surges = []
    for ctype in df[COL_TYPE].dropna().unique():
        sub = df[df[COL_TYPE] == ctype].groupby([COL_YEAR, COL_MONTH]).size().rename("건수")
        g = all_months.merge(sub.reset_index(), on=[COL_YEAR, COL_MONTH], how="left")
        g["건수"] = g["건수"].fillna(0)
        g = g.merge(monthly_total.reset_index(), on=[COL_YEAR, COL_MONTH])
        g["비중"] = g["건수"] / g["전체"]
        g = g.sort_values([COL_YEAR, COL_MONTH])
        if len(g) < 4:
            continue
        n_recent = max(1, len(g) // 4)
        baseline, recent = g["비중"].iloc[:-n_recent], g["비중"].iloc[-n_recent:]
        base_mean, recent_mean = baseline.mean(), recent.mean()
        if base_mean <= max_baseline_share and recent_mean >= min_recent_share:
            first_nonzero = g[g["건수"] > 0].iloc[0] if (g["건수"] > 0).any() else g.iloc[-n_recent]
            surges.append({
                "사건종별": ctype, "과거비중_평균": round(float(base_mean) * 100, 1),
                "최근비중_평균": round(float(recent_mean) * 100, 1),
                "최근시작": f"{int(first_nonzero[COL_YEAR])}-{int(first_nonzero[COL_MONTH]):02d}",
            })
    return pd.DataFrame(surges).sort_values("최근비중_평균", ascending=False) if surges \
        else pd.DataFrame(columns=["사건종별", "과거비중_평균", "최근비중_평균", "최근시작"])


def apply_corrections(df: pd.DataFrame, artifacts: pd.DataFrame,
                      surge_types: list[str]) -> pd.DataFrame:
    """
    '보정분석'용 데이터: 행정접수 아티팩트 (BASE,유형) 쌍과 제도변화형 급증 유형을
    제외한다. 재발가속·순찰추천은 반드시 이 보정 데이터로 계산해야 왜곡이 없다.
    (merge 기반 벡터 연산 — row-wise apply보다 대규모 데이터에서 훨씬 빠르다)
    """
    out = df.copy()
    if surge_types:
        out = out[~out[COL_TYPE].isin(surge_types)]
    if len(artifacts):
        bad = artifacts[[COL_BASE, COL_TYPE]].drop_duplicates().assign(_bad=True)
        out = out.merge(bad, on=[COL_BASE, COL_TYPE], how="left")
        out = out[out["_bad"].isna()].drop(columns="_bad")
    return out


# ═══════════════════════════════════════════════════════
# 5. 재발가속 탐지
# ═══════════════════════════════════════════════════════
def detect_acceleration(df: pd.DataFrame, min_reports: int = 4) -> pd.DataFrame:
    """
    지점별 재신고 간격(BASE_직전신고간격_일)을 시간순으로 반씩 나눠,
    최근 절반의 평균 간격이 과거 절반보다 뚜렷이 짧아진 지점을 '재발가속'으로 표시.
    """
    if COL_GAP_BASE not in df.columns:
        return pd.DataFrame(columns=[COL_BASE, "과거평균간격_일", "최근평균간격_일", "가속배율"])

    rows = []
    d = df.sort_values([COL_BASE, "_MSEQ_KEY"])
    for base, g in d.groupby(COL_BASE):
        gaps = g[COL_GAP_BASE].dropna().to_numpy()
        if len(gaps) < min_reports:
            continue
        half = len(gaps) // 2
        past, recent = gaps[:half], gaps[half:]
        if len(past) == 0 or len(recent) == 0:
            continue
        past_mean, recent_mean = past.mean(), recent.mean()
        if past_mean <= 0:
            continue
        ratio = recent_mean / past_mean
        if ratio < 0.7:  # 최근 간격이 과거의 70% 미만으로 짧아짐 = 가속
            rows.append({
                COL_BASE: base, "과거평균간격_일": round(float(past_mean), 1),
                "최근평균간격_일": round(float(recent_mean), 1),
                "가속배율": round(float(ratio), 2),
            })
    return pd.DataFrame(rows).sort_values("가속배율") if rows else pd.DataFrame(
        columns=[COL_BASE, "과거평균간격_일", "최근평균간격_일", "가속배율"])


# ═══════════════════════════════════════════════════════
# 6. 지점별 AI 판정 라벨링 (레거시 — classify_tracks가 이를 감싸 최종 트랙까지 만든다)
# ═══════════════════════════════════════════════════════
def judge_locations(df: pd.DataFrame, conc: dict, artifacts: pd.DataFrame,
                    accel: pd.DataFrame, surge_types: list[str] | None = None) -> pd.DataFrame:
    """
    각 반복지점(신고 2건 이상)에 대해 하나의 판정 라벨을 부여한다.
    - 제도관리형: 지점의 주요유형이 (확인된) 제도변화형 급증 유형인 경우
    - 행정접수 아티팩트: detect_admin_artifacts에서 해당 (BASE,유형) 쏠림 확인된 지점
    - 재발가속: accel에 포함된 지점
    - 실제 반복수요: 그 외 일반 반복지점
    ※ '지역분산 신호'는 더 이상 자동으로 복지연계라 단정하지 않는다 — 시설(병원 등)
      일 가능성과 진짜 지역분산을 구분 못 하므로, classify_tracks에서
      detect_facility_suspects 결과와 결합해 '확인대기'로 사람에게 넘긴다.
    """
    summary = df.groupby(COL_BASE).agg(
        건수=(COL_BASE, "size"),
        주요유형=(COL_TYPE, lambda s: s.value_counts().index[0]),
        SITE다양성=(COL_SITE, "nunique") if COL_SITE in df.columns else (COL_BASE, "size"),
    ).reset_index()

    artifact_bases = set(artifacts[COL_BASE]) if len(artifacts) else set()
    accel_bases = set(accel[COL_BASE]) if len(accel) else set()
    surge_types = set(surge_types or [])

    def label(row):
        if row["주요유형"] in surge_types:
            return "제도관리형"
        if row[COL_BASE] in artifact_bases:
            return "행정접수 아티팩트"
        if row[COL_BASE] in accel_bases:
            return "재발가속"
        if row["건수"] >= 2:
            return "실제 반복수요"
        return "검토필요"

    summary["AI판정"] = summary.apply(label, axis=1)
    summary["개입검토"] = summary["주요유형"].map(INTERVENTION_MAP).fillna(DEFAULT_INTERVENTION)
    return summary.sort_values("건수", ascending=False)


# 시설(병원·숙박시설·복지시설 등)에서 발생하는, 시설 운영 성격상 반복될 수 있는
# 유형의 예시 목록. ⚠ 이 역시 관할 실무 검토가 필요한 조정 가능한 기본값이다.
FACILITY_PRONE_TYPES = ["변사자", "안전확인", "응급구조", "타기관인계"]

TAG_OPTIONS = ["실제 반복지점", "시설거점", "행정접수 거점", "확인 안 됨"]
FACILITY_SUBTYPES = ["병원", "숙박시설", "복지시설", "기타"]
DEFAULT_TAG_FILE = "location_tags.json"


# ═══════════════════════════════════════════════════════
# 6-b. 시설집중 거점 의심 탐지
# ═══════════════════════════════════════════════════════
def detect_facility_suspects(df: pd.DataFrame,
                             facility_prone_types: list[str] | None = None,
                             min_site_diversity: int = 5,
                             min_type_share: float = 0.5,
                             min_count: int = 15) -> pd.DataFrame:
    """
    '지역에 넓게 퍼진 진짜 반복'과 '한 시설 내부가 세분화된 것'은 SITE 다양성만
    으로는 구분되지 않는다(예: 병원 병동별 상세주소). 그래서 다음 두 조건을
    함께 보는 걸 1차 판별 신호로 삼는다:
      ① SITE_ID 다양성이 높다(min_site_diversity 이상)
      ② 사건종별이 시설 운영 성격의 유형(facility_prone_types)에 몰려있다
         (min_type_share 이상)
    시간대 균일도는 참고용 '보조지표'로만 함께 표시하고, 이것만으로 후보를
    가르거나 제외하지 않는다 — 시간분포만으로 시설 여부를 자동확정하면
    또 다른 오분류가 생길 수 있기 때문이다.
    이 함수는 어떤 지점도 자동으로 제외하지 않는다. '확인이 필요한 후보'만
    골라내고, 실제 분류는 경찰관의 태그 확인을 거쳐야 한다.
    """
    facility_prone_types = (
        facility_prone_types if facility_prone_types is not None else FACILITY_PRONE_TYPES
    )
    cols = [COL_BASE, "건수", "SITE다양성", "시설연관유형비중", "주요유형",
            "시간대균일도(참고)", "사유"]
    if COL_SITE not in df.columns:
        return pd.DataFrame(columns=cols)

    rows = []
    for base, g in df.dropna(subset=[COL_SITE]).groupby(COL_BASE):
        if len(g) < min_count:
            continue
        site_div = g[COL_SITE].nunique()
        if site_div < min_site_diversity:
            continue
        type_counts = g[COL_TYPE].value_counts(normalize=True)
        facility_share = float(type_counts[type_counts.index.isin(facility_prone_types)].sum())
        if facility_share < min_type_share:
            continue

        main_type = type_counts.index[0]
        uniformity = None
        if "접수시간대" in g.columns:
            hp = g["접수시간대"].value_counts(normalize=True).reindex(
                range(24), fill_value=0
            ).to_numpy()
            hp = hp[hp > 0]
            if len(hp):
                uniformity = float(-(hp * np.log(hp)).sum() / np.log(24))

        reason = (f"'{main_type}' 등 시설연관 유형 비중 {facility_share*100:.0f}% · "
                 f"세부위치(SITE) {site_div}개로 분산")
        if uniformity is not None:
            if uniformity >= 0.75:
                reason += " · 시간대 고른 편(참고)"
            elif uniformity < 0.5:
                reason += " · 시간대 다소 편중(참고, 시설이 아닐 수도 있음)"

        rows.append({
            COL_BASE: base, "건수": len(g), "SITE다양성": site_div,
            "시설연관유형비중": round(facility_share * 100, 1), "주요유형": main_type,
            "시간대균일도(참고)": round(uniformity, 2) if uniformity is not None else None,
            "사유": reason,
        })

    out = pd.DataFrame(rows)
    return out.sort_values("건수", ascending=False) if len(out) else pd.DataFrame(columns=cols)


# ═══════════════════════════════════════════════════════
# 6-c. 거점 태그 저장소 (로컬 JSON — PoC 단계, 실도입 시 DB화)
# ═══════════════════════════════════════════════════════
def load_tags(path: str = DEFAULT_TAG_FILE) -> dict:
    import json
    import os
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_tags(tags: dict, path: str = DEFAULT_TAG_FILE) -> None:
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tags, f, ensure_ascii=False, indent=2)


def upsert_tag(tags: dict, base_id: str, tag: str, facility_type: str | None = None,
              confirmer: str = "", ts: str = "", path: str = DEFAULT_TAG_FILE,
              source: str = "manual_tab", reason_text: str = "") -> dict:
    """
    태그를 등록/수정하고 즉시 파일에 저장한다. tags 딕셔너리를 그대로 반환.
    source: 'manual_tab'(거점 유형 확인 탭에서 직접 선택) | 'assistant_chat'(대화로 학습)
    reason_text: 등록 근거가 된 원문(예: 어시스턴트에게 알려준 문장)
    """
    entry = {"태그": tag, "확인자": confirmer, "확인시각": ts, "출처": source}
    if reason_text:
        entry["등록근거"] = reason_text
    if tag == "시설거점" and facility_type:
        entry["시설유형"] = facility_type
    tags[base_id] = entry
    save_tags(tags, path)
    return tags


def delete_tag(tags: dict, base_id: str, path: str = DEFAULT_TAG_FILE) -> dict:
    """태그를 삭제하고 즉시 파일에 반영한다. 태그가 없으면 아무 동작 안 함."""
    tags.pop(base_id, None)
    save_tags(tags, path)
    return tags


# 경찰관이 확인한 태그 → 최종 트랙 매핑 (데이터는 지우지 않고 트랙만 분리)
TRACK_FROM_TAG = {
    "실제 반복지점": "맞춤형 순찰",
    "시설거점": "시설대응/협업",
    "행정접수 거점": "업무량 통계",
    # '확인 안 됨'은 명시적으로 선택해도 자동판정 경로로 그대로 넘어간다
}
# AI 자동판정 라벨 → 기본 트랙 (태그가 없거나 '확인 안 됨'일 때만 적용)
TRACK_FROM_LABEL = {
    "행정접수 아티팩트": "업무량 통계",
    "제도관리형": "업무량 통계",
    "시설의심(확인대기)": "확인대기",
    "재발가속": "맞춤형 순찰",
    "실제 반복수요": "맞춤형 순찰",
    "검토필요": "확인대기",
}


# ═══════════════════════════════════════════════════════
# 6-d. 거점 유형 최종 판정 — AI 후보제시 → 경찰관 확인 → 태그 반영
# ═══════════════════════════════════════════════════════
def classify_tracks(df: pd.DataFrame, artifacts: pd.DataFrame,
                    confirmed_surge_types: list[str], facility_suspects: pd.DataFrame,
                    accel: pd.DataFrame, tags: dict) -> pd.DataFrame:
    """
    지점(BASE_ID)별로 최종 트랙 하나를 정한다. 원칙:
      1) 경찰관이 태그를 확인해뒀으면(실제 반복지점/시설거점/행정접수 거점) 그
         태그가 AI 자동판정을 항상 덮어쓴다.
      2) 태그가 없거나 '확인 안 됨'이면 AI 자동판정(제도관리형 > 행정접수
         아티팩트 > 시설의심 > 재발가속 > 실제 반복수요 > 검토필요 순 우선)을 따른다.
    반환 컬럼: LOC_BASE_ID, 건수, 주요유형, 트랙, 판정사유, 원천, 시설유형
      트랙 ∈ {맞춤형 순찰, 시설대응/협업, 업무량 통계, 확인대기}
    """
    summary = df.groupby(COL_BASE).agg(
        건수=(COL_BASE, "size"),
        주요유형=(COL_TYPE, lambda s: s.value_counts().index[0]),
        SITE다양성=(COL_SITE, "nunique") if COL_SITE in df.columns else (COL_BASE, "size"),
    ).reset_index()

    artifact_bases = set(artifacts[COL_BASE]) if len(artifacts) else set()
    accel_bases = set(accel[COL_BASE]) if len(accel) else set()
    facility_bases = set(facility_suspects[COL_BASE]) if len(facility_suspects) else set()
    facility_reason = (
        facility_suspects.set_index(COL_BASE)["사유"].to_dict() if len(facility_suspects) else {}
    )
    surge_types = set(confirmed_surge_types or [])

    def auto_label(row):
        if row["주요유형"] in surge_types:
            return "제도관리형"
        if row[COL_BASE] in artifact_bases:
            return "행정접수 아티팩트"
        if row[COL_BASE] in facility_bases:
            return "시설의심(확인대기)"
        if row[COL_BASE] in accel_bases:
            return "재발가속"
        if row["건수"] >= 2:
            return "실제 반복수요"
        return "검토필요"

    summary["AI판정"] = summary.apply(auto_label, axis=1)
    summary["개입검토"] = summary["주요유형"].map(INTERVENTION_MAP).fillna(DEFAULT_INTERVENTION)

    def finalize(row):
        base = row[COL_BASE]
        entry = tags.get(base)
        if entry and entry.get("태그") in TRACK_FROM_TAG:
            reason = entry["태그"]
            if entry.get("시설유형"):
                reason += f" · {entry['시설유형']}"
            confirmer = entry.get("확인자", "")
            ts = entry.get("확인시각", "")
            return pd.Series({
                "트랙": TRACK_FROM_TAG[entry["태그"]], "판정사유": reason,
                "원천": f"경찰관 확인 ({confirmer} {ts})".strip(),
                "시설유형": entry.get("시설유형"),
            })
        label = row["AI판정"]
        reason = facility_reason.get(base, label) if label == "시설의심(확인대기)" else label
        return pd.Series({
            "트랙": TRACK_FROM_LABEL.get(label, "확인대기"), "판정사유": reason,
            "원천": "AI 자동판정", "시설유형": None,
        })

    extra = summary.apply(finalize, axis=1)
    summary = pd.concat([summary, extra], axis=1)
    return summary.sort_values("건수", ascending=False)


# ═══════════════════════════════════════════════════════
# 7. 맞춤형 순찰 추천
# ═══════════════════════════════════════════════════════
def recommend_patrol(df: pd.DataFrame, tracks: pd.DataFrame, accel: pd.DataFrame,
                     top_n: int = 10) -> pd.DataFrame:
    """
    트랙이 '맞춤형 순찰'인 지점만 대상으로 삼는다(행정통계·시설대응·확인대기 제외).
    각 지점의 주요 발생 시간대를 함께 추천해 '추천 순찰시간대'를 만든다.
    """
    candidates = tracks[tracks["트랙"] == "맞춤형 순찰"].copy()
    if len(candidates) == 0:
        return candidates.assign(추천순찰시간대=[], 가속배율=[], 추천행동=[])

    accel_map = accel.set_index(COL_BASE)["가속배율"].to_dict() if len(accel) else {}
    candidates["가속배율"] = candidates[COL_BASE].map(accel_map)

    time_col = "시간대구간" if "시간대구간" in df.columns else None
    peak_time = {}
    if time_col:
        cand_bases = set(candidates[COL_BASE])
        for base, g in df.groupby(COL_BASE):
            if base in cand_bases:
                peak_time[base] = g[time_col].value_counts().index[0]
    candidates["추천순찰시간대"] = candidates[COL_BASE].map(peak_time).fillna("전 시간대")

    candidates = candidates.sort_values(
        ["가속배율", "건수"], ascending=[True, False], na_position="last"
    )

    def action(row):
        if pd.notna(row["가속배율"]) and row["가속배율"] < 0.7:
            return "즉시 방문 확인 권고"
        if row["판정사유"] == "실제 반복지점":
            return "관심순찰 (경찰관 확인 지점)"
        return "관심순찰"

    candidates["추천행동"] = candidates.apply(action, axis=1)
    return candidates.head(top_n)[
        [COL_BASE, "트랙", "판정사유", "원천", "건수", "주요유형", "추천순찰시간대",
         "가속배율", "추천행동", "개입검토"]
    ]


# ═══════════════════════════════════════════════════════
# 8. 교대 브리핑 TOP3 (사람 인계메모 최우선 원칙)
# ═══════════════════════════════════════════════════════
def build_top3(patrol: pd.DataFrame, handoff_notes: list[dict], top_n: int = 3) -> list[dict]:
    """
    handoff_notes: [{"장소코드":..., "긴급": bool, "내용":..., "작성자":..., "작성시각":...}, ...]
    원칙: 긴급 인계메모가 있는 지점은 AI 추천 순위와 무관하게 항상 최상단.
    """
    cards = []
    urgent = [n for n in handoff_notes if n.get("긴급")]
    urgent_bases = {n["장소코드"] for n in urgent if n.get("장소코드")}

    for n in urgent:
        cards.append({
            "장소코드": n.get("장소코드", "-"), "사유": "인계메모 긴급",
            "요약": n["내용"], "추천행동": "직접 방문·확인",
            "출처": f'{n.get("작성자","")} · {n.get("작성시각","")}',
        })

    for _, row in patrol.iterrows():
        if len(cards) >= top_n:
            break
        if row[COL_BASE] in urgent_bases:
            continue
        cards.append({
            "장소코드": row[COL_BASE], "사유": row["판정사유"],
            "요약": f'{row["주요유형"]} 반복 · 최근 {row["추천순찰시간대"]} 집중',
            "추천행동": row["추천행동"], "출처": row.get("원천", "AI 분석"),
        })

    return cards[:top_n]


# ═══════════════════════════════════════════════════════
# 9. 시간분할 검증 (연/월 순서 기준)
# ═══════════════════════════════════════════════════════
def split_validation(df: pd.DataFrame, top_k: int = 20,
                     exclude_types: list[str] | None = None) -> dict:
    d = df if not exclude_types else df[~df[COL_TYPE].isin(exclude_types)]
    mid = d["_MSEQ_KEY"].median()
    first, second = d[d["_MSEQ_KEY"] < mid], d[d["_MSEQ_KEY"] >= mid]

    top_first = first.groupby(COL_BASE).size().sort_values(ascending=False).head(top_k)
    top_places = set(top_first.index)
    sec_counts = second.groupby(COL_BASE).size()
    sec_repeat = set(sec_counts[sec_counts >= 2].index)
    hit = top_places & sec_repeat

    repeat_total = int(sec_counts[sec_counts.index.isin(sec_repeat)].sum())
    repeat_covered = int(sec_counts[sec_counts.index.isin(hit)].sum())
    n_all = d[COL_BASE].nunique()

    return {
        "top_k": top_k, "hit_rate": len(hit) / top_k if top_k else np.nan,
        "hit_places": len(hit), "coverage": repeat_covered / repeat_total if repeat_total else np.nan,
        "repeat_total": repeat_total, "repeat_covered": repeat_covered,
        "random_expect": top_k / n_all if n_all else np.nan, "n_all_places": n_all,
        "top_first_table": top_first,
        "second_counts": sec_counts.reindex(top_first.index).fillna(0).astype(int),
    }
