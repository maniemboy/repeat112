# -*- coding: utf-8 -*-
"""
리핏112 (RE:PEAT 112) — v3 스키마 검증용 가상 데이터 생성기
================================================================
실제 업무데이터(Repeat112_PowerFew_분석용_v3.xlsx)와 동일한 컬럼 구조를
재현한 가상 데이터를 만든다. 코드 검증 전용이며 실제 수치와 무관하다.

실제 파일을 쓰려면: 이 스크립트로 만든 파일 대신, 실데이터 xlsx의
'분석데이터' 시트를 그대로 app.py에 업로드하면 된다 (컬럼명이 이미 동일).
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)

N_NORMAL = 2400
N_REPEAT = 260
N_STALK_SITES = 100  # 스토킹 전자장치: 제도변화형 급증 재현
N_ADMIN_SITES = 2    # 행정접수 아티팩트(분실습득/변사자류) 재현
N_FACILITY_LOCS = 1  # 시설(예: 대형병원) 시나리오 재현 — 여러 SITE에 걸친 시설연관 유형 집중

TYPES_NORMAL = {
    "질서유지": 0.26, "기타업무": 0.24, "일반범죄": 0.22,
    "교통": 0.21, "중요범죄": 0.06, "재해.재난": 0.01,
}
SUBTYPES = {
    "질서유지": ["행패소란", "위험방지", "시비"],
    "기타업무": ["상담문의", "내용확인불가", "서비스요청"],
    "일반범죄": ["기타형사범", "절도", "폭행"],
    "교통": ["교통사고", "교통불편"],
    "중요범죄": ["가정폭력", "스토킹", "성폭력"],
    "재해.재난": ["화재", "붕괴위험"],
}
CODES = ["C0", "C1", "C2", "C3", "C4"]
CODE_P = [0.02, 0.30, 0.45, 0.15, 0.08]
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
DONGS = [f"{n}동" for n in ["형곡1", "형곡2", "송정", "원평", "황상", "invalid"][:5]]


def _month_seq():
    """2025-05 ~ 2026-08, (연도, 월) 목록"""
    out = []
    y, m = 2025, 5
    while (y, m) <= (2026, 8):
        out.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


MONTHS = _month_seq()


def _rand_month():
    idx = RNG.integers(0, len(MONTHS))
    return MONTHS[idx]


def _base_row(loc_id, category=None):
    y, m = _rand_month()
    if category is None:
        category = RNG.choice(list(TYPES_NORMAL.keys()), p=list(TYPES_NORMAL.values()))
    subtype = RNG.choice(SUBTYPES[category])
    hour = int(RNG.integers(0, 24))
    return {
        "CASE_ID": None,
        "연도": y, "월": m, "월순번": int(RNG.integers(1, 400)),
        "요일": RNG.choice(WEEKDAYS), "접수시간대": hour,
        "시간대구간": "야간" if hour >= 20 or hour < 6 else ("주간" if 6 <= hour < 18 else "저녁"),
        "주말여부": RNG.choice(["평일", "주말"], p=[0.71, 0.29]),
        "코드": RNG.choice(CODES, p=CODE_P),
        "접수유형": "112신고",
        "종별분류": category, "사건종별": subtype,
        "종결분류": RNG.choice(["현장종결", "인계", "귀가조치"]),
        "종결": "정상종결",
        "종결시사건코드": RNG.choice(CODES, p=CODE_P),
        "행정동": RNG.choice(DONGS),
        "LOC_BASE_ID": loc_id,
        "LOC_SITE_ID": f"SITE{RNG.integers(1, 3000):05d}",
        "위치정밀도": RNG.choice(["BASE+DETAIL", "BASE_ONLY"], p=[0.46, 0.54]),
        "접수→지령_초": float(RNG.integers(10, 180)),
        "지령→출동_초": float(RNG.integers(30, 400)),
        "출동→도착_초": float(RNG.integers(60, 900)),
        "접수→도착_초": float(RNG.integers(200, 1200)),
        "도착→종결_분": float(RNG.integers(5, 90)),
    }


def make_data() -> pd.DataFrame:
    rows = []

    # 1) 일반 지점 (거의 반복 없음)
    for i in range(N_NORMAL):
        loc = f"BASE{i+1:05d}"
        n = int(RNG.choice([1, 1, 1, 2, 2, 3], p=[0.5, 0.2, 0.1, 0.12, 0.05, 0.03]))
        for _ in range(n):
            rows.append(_base_row(loc))

    # 2) 진짜 반복지점(Power Few) — 가정폭력/주취 등 중심 반복
    #    현실적으로 같은 주소(같은 세부지점)에서 반복되므로 SITE_ID를 고정한다.
    #    → '유형과 무관하게 SITE집중도만' 보는 판별식이면 이런 진짜 반복지점도
    #      아티팩트로 오탐되는지 확인하기 위한 시나리오.
    offset = N_NORMAL
    for i in range(N_REPEAT):
        loc = f"BASE{offset+i+1:05d}"
        fixed_site = f"SITE{50000+i:05d}"
        n = int(RNG.integers(5, 90))
        forced_cat = RNG.choice(["중요범죄", "질서유지"], p=[0.4, 0.6])
        for _ in range(n):
            row = _base_row(loc, category=forced_cat)
            row["LOC_SITE_ID"] = fixed_site
            rows.append(row)

    # 3) 스토킹 전자장치: 2026-06 이후에만 집중 발생 (제도변화형)
    offset2 = offset + N_REPEAT
    for i in range(N_STALK_SITES):
        loc = f"BASE{offset2+i+1:05d}"
        n = int(RNG.integers(3, 25))
        for _ in range(n):
            y, m = (2026, int(RNG.choice([6, 7, 8])))
            row = _base_row(loc, category="중요범죄")
            row.update({"연도": y, "월": m, "종별분류": "중요범죄", "사건종별": "스토킹 전자장치"})
            rows.append(row)

    # 4) 행정접수 아티팩트: 단일 SITE_ID에 몰린 분실습득/변사자
    offset3 = offset2 + N_STALK_SITES
    admin_cats = ["분실습득", "변사자"]
    for i in range(N_ADMIN_SITES):
        loc = f"BASE{offset3+i+1:05d}"
        fixed_site = f"SITE{90000+i:05d}"
        n = int(RNG.integers(150, 400))
        cat = admin_cats[i % len(admin_cats)]
        for _ in range(n):
            row = _base_row(loc, category="기타업무" if cat == "분실습득" else "질서유지")
            row["사건종별"] = cat
            row["LOC_SITE_ID"] = fixed_site  # 단일 창구 좌표로 고정
            row["위치정밀도"] = "BASE+DETAIL"
            rows.append(row)

    # 5) 시설(예: 대형병원) 시나리오 — 한 BASE지만 병동/구역별로 SITE_ID가
    #    여러 개(넓게 분산)이고, 시설연관 유형(변사자·응급구조·안전확인 등)에
    #    쏠려있으며, 시간대는 비교적 고르게 퍼짐(응급은 24시간 발생)
    offset4 = offset3 + N_ADMIN_SITES
    facility_cats = ["변사자", "안전확인", "응급구조", "타기관인계"]
    for i in range(N_FACILITY_LOCS):
        loc = f"BASE{offset4+i+1:05d}"
        n = int(RNG.integers(120, 220))
        n_sites = int(RNG.integers(15, 30))  # 병동/구역별 세부주소
        site_pool = [f"SITE{80000+i*100+j:05d}" for j in range(n_sites)]
        for _ in range(n):
            row = _base_row(loc, category="기타업무")
            row["사건종별"] = RNG.choice(facility_cats, p=[0.35, 0.3, 0.25, 0.1])
            row["LOC_SITE_ID"] = RNG.choice(site_pool)
            row["위치정밀도"] = "BASE+DETAIL"
            row["접수시간대"] = int(RNG.integers(0, 24))  # 시간대 고르게(응급 특성)
            rows.append(row)

    df = pd.DataFrame(rows)
    df["CASE_ID"] = [f"C{idx+1:06d}" for idx in range(len(df))]

    # 정렬 키 부여 후 시간 순서 재계산(월순번을 월 내 상대순서로 재부여)
    month_order = {m: i for i, m in enumerate(MONTHS)}
    df["_month_idx"] = df.apply(lambda r: month_order[(r["연도"], r["월"])], axis=1)
    df = df.sort_values(["_month_idx"]).reset_index(drop=True)
    df["월순번"] = df.groupby(["연도", "월"]).cumcount() + 1

    # BASE/SITE 반복지표 계산 (실데이터와 동일한 파생 방식)
    df = df.sort_values(["LOC_BASE_ID", "_month_idx", "월순번"]).reset_index(drop=True)
    df["BASE_전체신고건수"] = df.groupby("LOC_BASE_ID")["CASE_ID"].transform("count")
    df["BASE_반복여부"] = df["BASE_전체신고건수"] >= 2
    df["BASE_신고순번"] = df.groupby("LOC_BASE_ID").cumcount() + 1
    seq_idx = df.groupby("LOC_BASE_ID").cumcount()
    df["_seq_key"] = df["_month_idx"] * 1000 + df["월순번"]
    df["BASE_직전신고간격_일"] = (
        df.groupby("LOC_BASE_ID")["_seq_key"].diff() * (30 / 1000)
    ).round(2)
    df.loc[df["BASE_직전신고간격_일"] < 0, "BASE_직전신고간격_일"] = np.nan

    df = df.sort_values(["LOC_SITE_ID", "_month_idx", "월순번"]).reset_index(drop=True)
    df["SITE_전체신고건수"] = df.groupby("LOC_SITE_ID")["CASE_ID"].transform("count")
    df["SITE_반복여부"] = df["SITE_전체신고건수"] >= 2
    df["SITE_신고순번"] = df.groupby("LOC_SITE_ID").cumcount() + 1
    df["_seq_key2"] = df["_month_idx"] * 1000 + df["월순번"]
    df["SITE_직전신고간격_일"] = (
        df.groupby("LOC_SITE_ID")["_seq_key2"].diff() * (30 / 1000)
    ).round(2)
    df.loc[df["SITE_직전신고간격_일"] < 0, "SITE_직전신고간격_일"] = np.nan

    df = df.drop(columns=["_month_idx", "_seq_key", "_seq_key2"])
    df = df.sample(frac=1, random_state=3).reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = make_data()
    df.to_csv("sample_v3_data.csv", index=False, encoding="utf-8-sig")
    print(f"생성 완료: sample_v3_data.csv ({len(df):,}건, "
          f"BASE지점 {df['LOC_BASE_ID'].nunique()}개)")
