# -*- coding: utf-8 -*-
"""
리핏112 (RE:PEAT 112) — Streamlit 메인 앱
================================================================
실행:  streamlit run app.py
"""

from datetime import datetime
import os

import pandas as pd
import streamlit as st

# ── 샘플 데이터 자동 생성 (Streamlit Cloud 배포 시) ──────
if not os.path.exists("sample_v3_data.csv"):
    import generate_sample_v3
    generate_sample_v3.make_data().to_csv(
        "sample_v3_data.csv", index=False, encoding="utf-8-sig"
    )

import analysis as A
import assistant as AS
import map_view as MV

import map_view as MV

st.set_page_config(page_title="RE:PEAT 112 · 형곡지구대", page_icon="🚔",
                   layout="wide", initial_sidebar_state="collapsed")

BLUE   = "#1B4FBB"
BLUE_L = "#E8EEFA"
RED    = "#DC2626"
RED_L  = "#FEF2F2"
AMBER  = "#D97706"
AMB_L  = "#FFFBEB"
GREEN  = "#16A34A"
GRN_L  = "#F0FDF4"
GRAY   = "#6B7280"
NAVY   = "#12203D"

CSS = """
<style>
:root{
  --bg:#F5F6FA; --surface:#FFFFFF; --border:#E8EAF0;
  --blue:#1B4FBB; --blue-l:#EBF0FB; --blue-mid:#2563EB;
  --red:#DC2626; --red-l:#FEF2F2;
  --amber:#D97706; --amb-l:#FFFBEB;
  --green:#16A34A; --grn-l:#F0FDF4;
  --ink:#1A1D23; --sub:#4B5563; --muted:#9CA3AF;
  --sidebar:220px;
  --mono:ui-monospace,"SFMono-Regular","Consolas",monospace;
  --sans:-apple-system,"Apple SD Gothic Neo","Malgun Gothic","Segoe UI",sans-serif;
  --shadow:0 1px 3px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.04);
  --radius:10px;
}
html,body,[class*="css"],[class*="st-"]{font-family:var(--sans);color:var(--ink);}
.stApp{background:var(--bg)!important;}
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important;visibility:hidden!important;}
.block-container{padding:0!important;max-width:100%!important;}
[data-testid="stTabs"]>div:first-child{display:none!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-thumb{background:#D1D5DB;border-radius:4px;}
section[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important;min-width:var(--sidebar)!important;max-width:var(--sidebar)!important;}
section[data-testid="stSidebar"] .stMarkdown p{font-size:.82rem;color:var(--sub);}
section[data-testid="stSidebar"] label{font-size:.8rem!important;color:var(--sub)!important;}
.ax-topbar{background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 28px;height:52px;position:sticky;top:0;z-index:200;box-shadow:0 1px 3px rgba(0,0,0,.06);}
.ax-logo{display:flex;align-items:center;gap:10px;padding-right:24px;border-right:1px solid var(--border);margin-right:24px;}
.ax-logo-icon{width:30px;height:30px;border-radius:7px;background:var(--blue);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:.72rem;}
.ax-logo-text .l1{font-weight:700;color:var(--ink);font-size:.84rem;display:block;}
.ax-logo-text .l2{font-size:.69rem;color:var(--muted);display:block;}
.ax-nav{display:flex;gap:0;flex:1;height:100%;}
.ax-nav-item{height:100%;display:flex;align-items:center;padding:0 14px;font-size:.81rem;color:var(--muted);cursor:pointer;white-space:nowrap;border-bottom:2px solid transparent;margin-bottom:-1px;}
.ax-nav-item.active{color:var(--blue);border-bottom-color:var(--blue);font-weight:600;}
.ax-topbar-right{display:flex;align-items:center;gap:12px;font-size:.76rem;color:var(--muted);white-space:nowrap;margin-left:auto;}
.ax-badge{background:var(--blue-l);color:var(--blue);font-size:.69rem;font-weight:700;padding:3px 10px;border-radius:20px;}
.ax-main{padding:28px 32px 48px;max-width:1400px;margin:0 auto;}
.ax-page-header{margin-bottom:24px;}
.ax-page-title{font-size:1.22rem;font-weight:700;color:var(--ink);margin:0 0 4px;}
.ax-page-meta{font-size:.76rem;color:var(--muted);margin:0;}
.ax-kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:24px;}
.ax-kpi{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:22px 24px;box-shadow:var(--shadow);display:flex;align-items:flex-start;justify-content:space-between;}
.ax-kpi .kpi-label{font-size:.72rem;color:var(--muted);font-weight:500;margin-bottom:8px;letter-spacing:.02em;}
.ax-kpi .kpi-val{font-size:2.1rem;font-weight:700;line-height:1;margin-bottom:6px;font-family:var(--mono);}
.ax-kpi .kpi-sub{font-size:.71rem;color:var(--muted);line-height:1.4;}
.ax-kpi .kpi-icon{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.15rem;flex-shrink:0;margin-top:2px;}
.kpi-blue .kpi-val{color:var(--blue);} .kpi-blue .kpi-icon{background:var(--blue-l);}
.kpi-red .kpi-val{color:var(--red);} .kpi-red .kpi-icon{background:var(--red-l);}
.kpi-amber .kpi-val{color:var(--amber);} .kpi-amber .kpi-icon{background:var(--amb-l);}
.kpi-green .kpi-val{color:var(--green);} .kpi-green .kpi-icon{background:var(--grn-l);}
.kpi-gray .kpi-val{color:var(--sub);} .kpi-gray .kpi-icon{background:#F3F4F6;}
.ax-section{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden;margin-bottom:20px;}
.ax-section-head{display:flex;align-items:center;justify-content:space-between;padding:16px 22px;border-bottom:1px solid var(--border);}
.ax-section-head h3{font-size:.9rem;font-weight:700;color:var(--ink);margin:0;display:flex;align-items:center;gap:8px;}
.sh-badge{background:var(--blue-l);color:var(--blue);font-size:.68rem;font-weight:700;padding:2px 9px;border-radius:20px;}
.ax-section-body{padding:20px 22px;}
.ax-section-link{font-size:.76rem;color:var(--blue);cursor:pointer;}
.ax-patrol-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.ax-patrol-card{border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;background:var(--surface);}
.ax-patrol-card .pc-top{padding:14px 18px 12px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px;}
.ax-patrol-card .pc-rank{width:24px;height:24px;border-radius:50%;background:var(--blue);color:#fff;font-family:var(--mono);font-size:.72rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.ax-patrol-card.urgent .pc-rank{background:var(--red);}
.ax-patrol-card .pc-id{font-family:var(--mono);font-size:.92rem;font-weight:700;color:var(--ink);}
.ax-patrol-card .pc-type{font-size:.72rem;background:#F3F4F6;color:var(--sub);border-radius:5px;padding:2px 8px;white-space:nowrap;}
.ax-patrol-card .pc-body{padding:14px 18px;}
.ax-patrol-card .pc-chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;}
.ax-chip{font-size:.7rem;padding:3px 9px;border-radius:20px;background:#F3F4F6;color:var(--sub);border:1px solid var(--border);}
.ax-chip.blue{background:var(--blue-l);color:var(--blue);border-color:#BFD1F6;}
.ax-chip.red{background:var(--red-l);color:var(--red);border-color:#FECACA;}
.ax-chip.amber{background:var(--amb-l);color:var(--amber);border-color:#FDE68A;}
.ax-patrol-card .pc-action{font-size:.8rem;font-weight:700;color:var(--blue);}
.ax-patrol-card.urgent .pc-action{color:var(--red);}
.ax-summary-list{display:flex;flex-direction:column;}
.ax-summary-row{display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);font-size:.82rem;}
.ax-summary-row:last-child{border-bottom:none;}
.ax-summary-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:5px;}
.dot-red{background:var(--red);} .dot-amber{background:var(--amber);}
.dot-blue{background:var(--blue);} .dot-gray{background:#D1D5DB;}
.ax-summary-row .sr-body{flex:1;line-height:1.5;color:var(--sub);}
.ax-summary-row .sr-body b{color:var(--ink);}
.ax-bar-row{display:flex;align-items:center;gap:12px;margin-bottom:10px;}
.ax-bar-label{font-size:.78rem;color:var(--sub);width:60px;flex-shrink:0;}
.ax-bar-track{flex:1;height:9px;background:#F3F4F6;border-radius:5px;overflow:hidden;}
.ax-bar-fill{height:100%;border-radius:5px;}
.ax-bar-val{font-size:.75rem;color:var(--muted);width:38px;text-align:right;flex-shrink:0;font-family:var(--mono);}
.ax-pf-row{display:flex;align-items:baseline;gap:10px;margin-bottom:12px;}
.ax-pf-pct{font-family:var(--mono);font-size:1.7rem;font-weight:800;color:var(--blue);}
.ax-pf-desc{font-size:.82rem;color:var(--muted);}
.ax-judge-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.ax-judge-item{border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px;background:var(--surface);}
.ax-judge-item .ji-label{font-size:.72rem;color:var(--muted);margin-bottom:5px;}
.ax-judge-item .ji-val{font-family:var(--mono);font-size:1.3rem;font-weight:700;color:var(--ink);}
.ax-judge-item .ji-sub{font-size:.7rem;color:var(--muted);margin-top:2px;}
.ax-judge-item.red{border-left:3px solid var(--red);}
.ax-judge-item.blue{border-left:3px solid var(--blue);}
.ax-judge-item.amber{border-left:3px solid var(--amber);}
.ax-judge-item.gray{border-left:3px solid #D1D5DB;}
.ax-tab-body{padding:0 32px 40px;max-width:1400px;margin:0 auto;}
.ax-panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:22px 24px;margin-bottom:16px;}
.ax-panel h4{font-size:.9rem;font-weight:700;color:var(--ink);margin:0 0 14px;}
.rp-note{color:var(--muted);font-size:.82rem;line-height:1.6;}
.badge{display:inline-block;font-size:.74rem;padding:3px 10px;border-radius:5px;margin:2px 3px 2px 0;}
.b-real{background:var(--blue-l);color:var(--blue);}
.b-accel{background:var(--red-l);color:var(--red);}
.b-region{background:var(--grn-l);color:var(--green);}
.b-admin{background:#F9FAFB;color:var(--muted);}
.b-inst{background:#F5F3FF;color:#6D28D9;}
.b-review{background:#F9FAFB;color:var(--muted);}
.headline-card{border-radius:var(--radius);padding:18px 20px;}
.hc-urgent{background:var(--red-l);border:1px solid #FECACA;}
.hc-accel{background:var(--amb-l);border:1px solid #FDE68A;}
.hc-normal{background:var(--blue-l);border:1px solid #BFD1F6;}
.brief-tag{font-family:var(--mono);font-size:.68rem;padding:2px 8px;border-radius:5px;color:#fff;display:inline-block;margin-bottom:8px;}
.note-row{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);font-size:.83rem;}
[data-testid="stMetricValue"]{font-family:var(--mono)!important;}
[data-baseweb="tab-highlight"]{background-color:var(--blue)!important;}
button[data-baseweb="tab"][aria-selected="true"] p{color:var(--blue)!important;font-weight:700!important;}
[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:var(--radius)!important;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def badge(text, cls):
    return f'<span class="badge {cls}">{text}</span>'


def metric_cards(items):
    """기존 탭 내부에서 사용하는 간이 지표 카드 (호환성 유지)."""
    cells = "".join(
        f'<div style="background:#fff;border:1px solid #DDD9D0;border-left:4px solid {c};'
        f'border-radius:10px;padding:12px 14px;">'
        f'<div style="font-size:.72rem;color:#677080;margin-bottom:4px">{l}</div>'
        f'<div style="font-family:ui-monospace,monospace;font-size:1.4rem;font-weight:700;color:#12203D">{v}</div>'
        f'<div style="font-size:.7rem;color:#9AA0A8;margin-top:3px">{cap}</div></div>'
        for l, v, cap, c in items
    )
    st.markdown(
        f'<div style="display:grid;gap:10px;margin:6px 0 14px;'
        f'grid-template-columns:repeat(auto-fit,minmax(160px,1fr))">{cells}</div>',
        unsafe_allow_html=True,
    )


BADGE_CLS = {
    "실제 반복수요": "b-real", "재발가속": "b-accel", "지역분산 신호": "b-region",
    "행정접수 아티팩트": "b-admin", "제도관리형": "b-inst", "검토필요": "b-review",
    "시설의심(확인대기)": "b-region",
    "맞춤형 순찰": "b-real", "시설대응/협업": "b-inst", "업무량 통계": "b-admin",
    "확인대기": "b-review",
}


def nav_bar(current_tab: str, tab_list: list, data_label: str, ts: str):
    tabs_html = "".join(
        f'<div class="rp-nav-tab {"active" if t == current_tab else ""}" '
        f'onclick="document.querySelector(\'[data-testid=\\\"stSelectbox\\\"]\')">{t}</div>'
        for t in tab_list
    )
    st.markdown(
        f'<div class="rp-nav">'
        f'<div class="rp-logo">RE:PEAT <span>112</span></div>'
        f'<div class="rp-nav-tabs">{tabs_html}</div>'
        f'<div class="rp-nav-right">{data_label} · {ts}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_head(title: str, count: str = "", link_text: str = ""):
    link = f'<span class="sh-link">{link_text}</span>' if link_text else ""
    cnt = f'<span class="sh-count">{count}</span>' if count else ""
    st.markdown(
        f'<div class="rp-section-head">'
        f'<h2>{title}</h2>{cnt}'
        f'<div class="rp-divider"></div>{link}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── 데이터 업로드 (사이드바 스타일 숨김 처리) ─────────
uploaded = None
use_sample = True
with st.sidebar:
    st.markdown("**데이터 업로드**")
    uploaded = st.file_uploader("분석용 데이터 (xlsx/csv)", type=["xlsx", "csv"],
                                label_visibility="collapsed")
    use_sample = st.checkbox("샘플 데이터로 시연", value=uploaded is None)
    st.caption("🔒 비식별·최소화된 자료만 사용")


@st.cache_data
def load_sample():
    return pd.read_csv("sample_v3_data.csv")


def load_uploaded(f):
    if f.name.endswith(".xlsx"):
        try:
            return pd.read_excel(f, sheet_name="분석데이터")
        except ValueError:
            return pd.read_excel(f)
    return pd.read_csv(f)


if uploaded is not None:
    raw = load_uploaded(uploaded)
    src_label = f"업로드 파일 ({uploaded.name})"
elif use_sample:
    raw = load_sample()
    src_label = "내장 샘플 데이터 (가상 · 시연용)"
else:
    st.info("좌측에서 데이터를 업로드하거나 샘플 데이터를 선택하세요.")
    st.stop()

diag = A.diagnose(raw)
if diag["missing_columns"]:
    st.error(f"필수 컬럼 없음: {diag['missing_columns']} — 컬럼명을 확인하세요.")
    st.stop()

@st.cache_data(show_spinner=False)
def _cached_clean(raw_df):
    return A.clean(raw_df)


@st.cache_data(show_spinner=False)
def _cached_detections(clean_df):
    """태그·확인상태와 무관하게 데이터에서만 결정되는 탐지 결과는 캐싱해 재실행 속도를 높인다."""
    artifacts = A.detect_admin_artifacts(clean_df)
    surge_suspects = A.detect_institutional_surge(clean_df)
    facility_suspects = A.detect_facility_suspects(clean_df)
    return artifacts, surge_suspects, facility_suspects


clean_df, clean_log = _cached_clean(raw)

artifacts, surge_suspects, facility_suspects = _cached_detections(clean_df)

if "confirmed_surge_types" not in st.session_state:
    st.session_state.confirmed_surge_types = []
st.session_state.confirmed_surge_types = [
    t for t in st.session_state.confirmed_surge_types
    if t in surge_suspects["사건종별"].tolist()
]

# 거점 태그: 로컬 JSON에서 로드(재실행 후에도 유지), 세션에도 캐시
TAG_PATH = A.DEFAULT_TAG_FILE
if "location_tags" not in st.session_state:
    st.session_state.location_tags = A.load_tags(TAG_PATH)
if "confirmed_surge_types" not in st.session_state:
    st.session_state.confirmed_surge_types = []
if "mode" not in st.session_state:
    st.session_state.mode = "홈"
if "handoff_notes" not in st.session_state:
    st.session_state.handoff_notes = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_teach" not in st.session_state:
    st.session_state.pending_teach = None

st.session_state.confirmed_surge_types = [
    t for t in st.session_state.confirmed_surge_types
    if t in surge_suspects["사건종별"].tolist()
]

confirmed_surge_types = st.session_state.confirmed_surge_types
corrected_stage1 = A.apply_corrections(clean_df, artifacts, confirmed_surge_types)

conc_raw = A.concentration(clean_df)
accel = A.detect_acceleration(corrected_stage1)
tracks = A.classify_tracks(clean_df, artifacts, confirmed_surge_types, facility_suspects,
                           accel, st.session_state.location_tags)

# 보정 집중도: '맞춤형 순찰'+'확인대기' 트랙만 포함 (업무통계·시설대응은 확정 제외)
conc_pool_bases = set(tracks[tracks["트랙"].isin(["맞춤형 순찰", "확인대기"])][A.COL_BASE])
conc_pool = clean_df[clean_df[A.COL_BASE].isin(conc_pool_bases)]
conc_adj = A.concentration(conc_pool)

patrol = A.recommend_patrol(clean_df, tracks, accel, top_n=15)
map_points = MV.attach_dong(tracks, clean_df)  # Power Few Map용 — 행정동 부여(실좌표 아님)

if "handoff_notes" not in st.session_state:
    st.session_state.handoff_notes = []

top3 = A.build_top3(patrol, st.session_state.handoff_notes, top_n=3)


def render_home():
    """홈 탭 — AX Board 스타일 공공 상황판."""
    now_str = datetime.now().strftime("%Y.%m.%d %H:%M")
    n_total  = clean_log["final_rows"]
    n_accel  = len(accel)
    n_patrol = (tracks["트랙"] == "맞춤형 순찰").sum()
    n_pend   = (tracks["트랙"] == "확인대기").sum()
    n_excl   = len(clean_df) - len(conc_pool)
    pf5_share = conc_adj["top5"]["share"] * 100
    pf5_k     = conc_adj["top5"]["k_places"]

    # ── 앱바 ────────────────────────────────────────
    st.markdown(
        f'''<div class="ax-topbar">
          <div class="ax-logo">
            <div class="ax-logo-icon">112</div>
            <div class="ax-logo-text">
              <span class="l1">RE:PEAT 112</span>
              <span class="l2">형곡지구대 · 반복신고 수요 분석</span>
            </div>
          </div>
          <div class="ax-nav">
            <div class="ax-nav-item active">홈</div>
            <div class="ax-nav-item">분석</div>
            <div class="ax-nav-item">맞춤형 순찰</div>
            <div class="ax-nav-item">지도</div>
            <div class="ax-nav-item">브리핑</div>
            <div class="ax-nav-item">Assistant</div>
          </div>
          <div class="ax-topbar-right">
            <span class="ax-badge">POWER FEW 분석</span>
            기준일시 {now_str}
          </div>
        </div>''',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="ax-main">', unsafe_allow_html=True)

    # ── 1행: 페이지 헤더 ────────────────────────────
    st.markdown(
        f'''<div class="ax-page-header">
          <div>
            <p class="ax-page-title">공공 치안 AI 분석 현황</p>
            <p class="ax-page-meta">반복신고 수요 진단 및 개입 우선순위 시스템 · Power Few 기반 · {now_str} 자동생성</p>
          </div>
        </div>''',
        unsafe_allow_html=True,
    )

    # ── 2행: KPI 카드 5개 ────────────────────────────
    st.markdown(
        f'''<div class="ax-kpi-row">
          <div class="ax-kpi kpi-blue">
            <div class="kpi-left">
              <div class="kpi-label">전체 신고건수</div>
              <div class="kpi-val">{n_total:,}</div>
              <div class="kpi-sub">분석 대상 기간 전체</div>
            </div>
            <div class="kpi-icon">📋</div>
          </div>
          <div class="ax-kpi kpi-red">
            <div class="kpi-left">
              <div class="kpi-label">재발가속 지점</div>
              <div class="kpi-val">{n_accel}</div>
              <div class="kpi-sub">재신고 간격이 짧아진 곳</div>
            </div>
            <div class="kpi-icon">⚠️</div>
          </div>
          <div class="ax-kpi kpi-amber">
            <div class="kpi-left">
              <div class="kpi-label">Power Few 상위 5%</div>
              <div class="kpi-val">{pf5_share:.0f}%</div>
              <div class="kpi-sub">{pf5_k}곳 → 전체 신고의 {pf5_share:.0f}%</div>
            </div>
            <div class="kpi-icon">📊</div>
          </div>
          <div class="ax-kpi kpi-green">
            <div class="kpi-left">
              <div class="kpi-label">맞춤형 순찰 지점</div>
              <div class="kpi-val">{n_patrol}</div>
              <div class="kpi-sub">오늘 순찰 추천 대상</div>
            </div>
            <div class="kpi-icon">🚔</div>
          </div>
          <div class="ax-kpi kpi-gray">
            <div class="kpi-left">
              <div class="kpi-label">확인대기 지점</div>
              <div class="kpi-val">{n_pend}</div>
              <div class="kpi-sub">거점 유형 미확인 / 제외 {n_excl}건</div>
            </div>
            <div class="kpi-icon">🔍</div>
          </div>
        </div>''',
        unsafe_allow_html=True,
    )

    # ── 3행: 순찰 TOP3 + 상황 요약 ─────────────────
    c_patrol, c_summary = st.columns([2, 1])

    with c_patrol:
        top3 = patrol.head(3)
        cards_html = ""
        for i, (_, row) in enumerate(top3.iterrows(), 1):
            is_accel = pd.notna(row["가속배율"]) and row["가속배율"] < 0.7
            card_cls = "ax-patrol-card urgent" if is_accel else "ax-patrol-card"
            chip_accel = (f'<span class="ax-chip red">가속 {row["가속배율"]:.2f}</span>' if is_accel else "")
            cards_html += f'''
            <div class="{card_cls}">
              <div class="pc-top">
                <div class="pc-rank">{i}</div>
                <div class="pc-id">{row[A.COL_BASE]}</div>
                <div class="pc-type">{row["주요유형"]}</div>
              </div>
              <div class="pc-body">
                <div class="pc-chips">
                  <span class="ax-chip blue">{row["추천순찰시간대"]}</span>
                  <span class="ax-chip">{int(row["건수"])}건</span>
                  {chip_accel}
                </div>
                <div class="pc-action">▶ {row["추천행동"]}</div>
              </div>
            </div>'''
        st.markdown(
            f'''<div class="ax-section">
              <div class="ax-section-head">
                <h3>오늘의 맞춤형 순찰 TOP3 <span class="sh-badge">Power Few 기반</span></h3>
                <span class="ax-section-link">전체 보기 →</span>
              </div>
              <div class="ax-section-body">
                <div class="ax-patrol-grid">{cards_html}</div>
              </div>
            </div>''',
            unsafe_allow_html=True,
        )

    with c_summary:
        top_accel = accel.head(3)
        rows_html = ""
        for _, r in top_accel.iterrows():
            rows_html += f'''<div class="ax-summary-row">
              <div class="ax-summary-dot dot-red"></div>
              <div class="sr-body"><b>{r[A.COL_BASE]}</b> 재발가속 — 재신고 간격 {r["최근평균간격_일"]}일</div>
            </div>'''
        n_fac = (tracks["트랙"] == "시설대응/협업").sum()
        n_admin = (tracks["트랙"] == "업무량 통계").sum()
        rows_html += f'''
        <div class="ax-summary-row">
          <div class="ax-summary-dot dot-amber"></div>
          <div class="sr-body"><b>확인대기</b> {n_pend}곳 — 거점 유형 미확인</div>
        </div>
        <div class="ax-summary-row">
          <div class="ax-summary-dot dot-blue"></div>
          <div class="sr-body"><b>시설거점</b> {n_fac}곳 확인 / 행정접수 {n_admin}곳 분리</div>
        </div>
        <div class="ax-summary-row">
          <div class="ax-summary-dot dot-gray"></div>
          <div class="sr-body">지니계수 <b>{conc_adj["gini"]:.3f}</b> — 소수 지점 집중 강도</div>
        </div>'''
        st.markdown(
            f'''<div class="ax-section" style="height:100%">
              <div class="ax-section-head"><h3>핵심 상황 요약</h3></div>
              <div class="ax-section-body">
                <div class="ax-summary-list">{rows_html}</div>
              </div>
            </div>''',
            unsafe_allow_html=True,
        )

    # ── 4행: 지도 + 집중도 ────────────────────────────
    c_map, c_pf = st.columns([3, 2])

    with c_map:
        fmap = MV.apply_filter(map_points, "Power Few")
        map_svg = MV.render_map_svg(fmap, adapter=MV.SchematicAdapter(), height=280)
        st.markdown(
            f'''<div class="ax-section">
              <div class="ax-section-head">
                <h3>Power Few Map <span class="sh-badge">행정동 개략도 · 실좌표 아님</span></h3>
              </div>
              <div class="ax-section-body">{map_svg}</div>
            </div>''',
            unsafe_allow_html=True,
        )

    with c_pf:
        pf_rows = ""
        for p in (1, 5, 10):
            share = conc_adj[f"top{p}"]["share"] * 100
            k = conc_adj[f"top{p}"]["k_places"]
            pf_rows += (f'<div class="ax-pf-row">'
                       f'<div class="ax-pf-pct">{share:.1f}%</div>'
                       f'<div class="ax-pf-desc">상위 {p}% ({k}곳)</div></div>')
        st.markdown(
            f'''<div class="ax-section">
              <div class="ax-section-head">
                <h3>Power Few 집중도 <span class="sh-badge">지니 {conc_adj["gini"]:.3f}</span></h3>
              </div>
              <div class="ax-section-body">{pf_rows}</div>
            </div>''',
            unsafe_allow_html=True,
        )

    # ── 5행: 사건유형 분포 + 시간대 + AI판정 ─────────
    c_type, c_time, c_judge = st.columns([1, 1, 1])

    with c_type:
        type_dist = clean_df["종별분류"].value_counts()
        total_t = type_dist.sum()
        bar_colors = ["#1B4FBB","#2563EB","#60A5FA","#93C5FD","#BFDBFE"]
        bars = ""
        for i,(k,v) in enumerate(type_dist.head(5).items()):
            pct = v/total_t*100
            bars += f'''<div class="ax-bar-row">
              <div class="ax-bar-label">{k[:4]}</div>
              <div class="ax-bar-track"><div class="ax-bar-fill"
                style="width:{pct:.0f}%;background:{bar_colors[i%len(bar_colors)]};"></div></div>
              <div class="ax-bar-val">{pct:.0f}%</div>
            </div>'''
        st.markdown(
            '<div class="ax-section"><div class="ax-section-head"><h3>사건 유형 분포</h3></div>'
            '<div class="ax-section-body">' + bars + '</div></div>',
            unsafe_allow_html=True,
        )

    with c_time:
        if "시간대구간" in clean_df.columns:
            td = clean_df["시간대구간"].value_counts()
            total_td = td.sum()
            tc_map = {"주간":"#1B4FBB","저녁":"#D97706","야간":"#DC2626"}
            bars2 = ""
            for k,v in td.items():
                pct = v/total_td*100
                bars2 += f'''<div class="ax-bar-row">
                  <div class="ax-bar-label">{k}</div>
                  <div class="ax-bar-track"><div class="ax-bar-fill"
                    style="width:{pct:.0f}%;background:{tc_map.get(k,"#6B7280")};"></div></div>
                  <div class="ax-bar-val">{pct:.0f}%</div>
                </div>'''
        else:
            bars2 = "<p style='font-size:.78rem;color:#6B7280'>시간대 데이터 없음</p>"
        st.markdown(
            '<div class="ax-section"><div class="ax-section-head"><h3>시간대별 신고 분포</h3></div>'
            '<div class="ax-section-body">' + bars2 + '</div></div>',
            unsafe_allow_html=True,
        )

    with c_judge:
        n_real = (tracks["트랙"]=="맞춤형 순찰").sum()
        n_fac  = (tracks["트랙"]=="시설대응/협업").sum()
        n_stat = (tracks["트랙"]=="업무량 통계").sum()
        n_wa   = (tracks["트랙"]=="확인대기").sum()
        st.markdown(
            f'''<div class="ax-section">
              <div class="ax-section-head"><h3>AI 거점 판정 요약</h3></div>
              <div class="ax-section-body">
                <div class="ax-judge-grid">
                  <div class="ax-judge-item red">
                    <div class="ji-label">맞춤형 순찰</div>
                    <div class="ji-val">{n_real}</div>
                    <div class="ji-sub">진짜 반복지점</div>
                  </div>
                  <div class="ax-judge-item amber">
                    <div class="ji-label">확인대기</div>
                    <div class="ji-val">{n_wa}</div>
                    <div class="ji-sub">시설의심 등</div>
                  </div>
                  <div class="ax-judge-item blue">
                    <div class="ji-label">시설대응/협업</div>
                    <div class="ji-val">{n_fac}</div>
                    <div class="ji-sub">경찰관 확인됨</div>
                  </div>
                  <div class="ax-judge-item gray">
                    <div class="ji-label">업무량 통계</div>
                    <div class="ji-val">{n_stat}</div>
                    <div class="ji-sub">행정접수 거점</div>
                  </div>
                </div>
              </div>
            </div>''',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)  # ax-main 닫기



    # ── 맞춤형 순찰 TOP5 ───────────────────────────────
    section_head("오늘의 맞춤형 순찰 우선지점", count=f"TOP {min(5,len(patrol))}",
                 link_text="전체 목록 →")
    if len(patrol) == 0:
        st.caption("현재 맞춤형 순찰 추천 지점이 없습니다.")
    else:
        cards_html = ""
        for i, (_, row) in enumerate(patrol.head(5).iterrows(), 1):
            is_accel = pd.notna(row["가속배율"]) and row["가속배율"] < 0.7
            card_cls = "rp-patrol-card accel" if is_accel else "rp-patrol-card"
            chip_accel = (f'<span class="pc-chip accel">가속배율 {row["가속배율"]:.2f}</span>'
                         if is_accel else "")
            time_chip = f'<span class="pc-chip time">{row["추천순찰시간대"]}</span>'
            cnt_chip = f'<span class="pc-chip">{int(row["건수"])}건</span>'
            cards_html += f"""
            <div class="{card_cls}">
              <div class="pc-header">
                <div class="pc-rank">{i}</div>
                <div class="pc-id">{row[A.COL_BASE]}</div>
                <div class="pc-type">{row["주요유형"]}</div>
              </div>
              <div class="pc-body">
                <div class="pc-meta">{time_chip}{cnt_chip}{chip_accel}</div>
                <div class="pc-action">{row["추천행동"]}</div>
              </div>
            </div>"""
        st.markdown(
            f'<div class="rp-patrol-grid">{cards_html}</div>',
            unsafe_allow_html=True,
        )

    # ── Power Few 집중도 미니 ──────────────────────────
    c1, c2 = st.columns([1, 1])
    with c1:
        section_head("Power Few 집중도 (보정분석)")
        rows_html = "".join(
            f'<div class="pf-row">'
            f'<div class="pf-pct">{conc_adj[f"top{p}"]["share"]*100:.1f}%</div>'
            f'<div class="pf-desc">상위 {p}% ({conc_adj[f"top{p}"]["k_places"]}곳)</div>'
            f'</div>'
            for p in (1, 5, 10)
        )
        st.markdown(
            f'<div class="rp-pfcard">'
            f'<div class="pf-label">장소 집중도 · 지니계수 {conc_adj["gini"]:.3f}</div>'
            f'{rows_html}</div>',
            unsafe_allow_html=True,
        )
    with c2:
        section_head("로렌츠 곡선")
        ldf = pd.DataFrame({
            "지점 누적비율": conc_adj["lorenz_x"],
            "신고 누적비율": conc_adj["lorenz_y"],
            "균등기준선": conc_adj["lorenz_x"],
        }).set_index("지점 누적비율")
        st.line_chart(ldf, height=200)

    # ── 미니 지도 (행정동 개략도) ──────────────────────
    section_head("지점 분포 개략도")
    filtered_map = MV.apply_filter(map_points, "Power Few")
    st.markdown(
        MV.render_map_svg(filtered_map, adapter=MV.SchematicAdapter(), height=300),
        unsafe_allow_html=True,
    )
    st.caption("⚠ 실좌표가 아닌 행정동 기반 개략도입니다.")


def render_dashboard():
    """분석 탭 화면들."""

    tabs = st.tabs([
        "홈", "품질진단", "Power Few 집중도", "거점 유형 확인", "재발가속·순찰추천",
        "시간분할 검증", "TOP20 상세", "Power Few Map", "AI 어시스턴트",
    ])

    with tabs[0]:
        render_home()

    with tabs[1]:
        st.markdown("**데이터 품질 자동진단**")
        metric_cards([
            ("중복행", diag["duplicate_rows"], "완전 중복", RISK),
            ("코드 표기 오류", diag.get("code_anomalies", 0), "예: C1선→C1", AMBER),
            ("위치 결측 제외", clean_log["removed_no_location"], "장소코드 없음", NAVY),
            ("최종 분석건수", f"{clean_log['final_rows']:,}", "", CALM),
        ])

    with tabs[2]:
        st.markdown("**Power Few 집중도 — 원시 vs 보정**")
        view = st.radio(
            "기준", ["보정분석 (아티팩트·제도변화·시설거점 확정분 제외)", "원시분석"],
            horizontal=True,
        )
        conc = conc_adj if view.startswith("보정") else conc_raw
        cells = []
        for p in (1, 5, 10):
            d = conc[f"top{p}"]
            cells.append((f"상위 {p}% ({d['k_places']}곳)", f"{d['share']*100:.1f}%", "전체 신고 점유율", NAVY))
        cells.append(("지니계수", f"{conc['gini']:.3f}", "1에 가까울수록 집중", AMBER))
        metric_cards(cells)
        lorenz = pd.DataFrame({"지점누적비율": conc["lorenz_x"], "신고누적비율": conc["lorenz_y"],
                               "균등기준선": conc["lorenz_x"]}).set_index("지점누적비율")
        st.line_chart(lorenz, height=300)
        st.markdown(
            '<p class="rp-note">보정분석은 경찰관이 아직 확인하지 않은 "확인대기" 지점은 '
            "그대로 포함합니다(임의로 숨기지 않음) — 업무량 통계·시설대응으로 확정 태그된 "
            "지점만 제외합니다.</p>", unsafe_allow_html=True,
        )
        if len(surge_suspects):
            st.markdown("**제도변화형 급증 — 의심 후보 (좌측 사이드바에서 확인 체크 시 제외 반영)**")
            show = surge_suspects.copy()
            show["상태"] = show["사건종별"].apply(
                lambda t: "✅ 확인됨 (제외 반영)" if t in confirmed_surge_types else "⚠ 의심 (미확인 · 아직 포함)"
            )
            st.dataframe(show, use_container_width=True)
        if len(artifacts):
            st.markdown("**행정접수 아티팩트 (유형게이트+SITE집중도 2단계 자동판별)**")
            st.dataframe(artifacts, use_container_width=True)

    with tabs[3]:
        st.markdown("**거점 유형 확인** · AI가 후보를 제시하면 경찰관이 확인하고, "
                    "확인된 태그는 다음 근무조까지 그대로 유지됩니다.")
        track_counts = tracks["트랙"].value_counts()
        chips = "".join(badge(f"{k} · {v}곳", BADGE_CLS.get(k, "b-review")) for k, v in track_counts.items())
        st.markdown(chips, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**시설의심 후보 TOP10** (SITE 다양성 + 시설연관 유형 비중 기준, "
                    "시간대 균일도는 참고용 보조지표)")
        if len(facility_suspects):
            st.dataframe(facility_suspects.head(10), use_container_width=True)
        else:
            st.caption("탐지된 시설의심 후보가 없습니다.")

        st.markdown("---")
        st.markdown("**거점 태그 확인/등록**")
        c1, c2 = st.columns([2, 1])
        target = c1.selectbox(
            "장소 선택", tracks.sort_values("건수", ascending=False)[A.COL_BASE].tolist(),
            key="tag_target",
        )
        existing = st.session_state.location_tags.get(target)
        cur_row = tracks[tracks[A.COL_BASE] == target].iloc[0]
        c2.markdown(badge(cur_row["트랙"], BADGE_CLS.get(cur_row["트랙"], "b-review")),
                   unsafe_allow_html=True)
        st.caption(f"현재 판정사유: {cur_row['판정사유']} · 원천: {cur_row['원천']} · "
                  f"건수 {int(cur_row['건수'])} · 주요유형 {cur_row['주요유형']}")

        default_idx = A.TAG_OPTIONS.index(existing["태그"]) if existing else 3
        tag_choice = st.radio("태그 선택", A.TAG_OPTIONS, index=default_idx, horizontal=True,
                              key="tag_choice")
        facility_type = None
        if tag_choice == "시설거점":
            f_default = existing.get("시설유형", A.FACILITY_SUBTYPES[0]) if existing else A.FACILITY_SUBTYPES[0]
            facility_type = st.selectbox(
                "시설 세부유형", A.FACILITY_SUBTYPES,
                index=A.FACILITY_SUBTYPES.index(f_default) if f_default in A.FACILITY_SUBTYPES else 0,
            )
        confirmer = st.text_input("확인자", value=existing.get("확인자", "") if existing else "")

        if st.button("태그 저장"):
            st.session_state.location_tags = A.upsert_tag(
                st.session_state.location_tags, target, tag_choice,
                facility_type=facility_type, confirmer=confirmer.strip() or "미상",
                ts=datetime.now().strftime("%m/%d %H:%M"), path=TAG_PATH,
            )
            st.success(f"{target} → '{tag_choice}'"
                      f"{' · ' + facility_type if facility_type else ''} 저장 완료")
            st.rerun()

        if st.session_state.location_tags:
            st.markdown("**저장된 태그 목록** (등록시간·등록근거 포함)")
            tag_view = pd.DataFrame([
                {"장소코드": k, **v} for k, v in st.session_state.location_tags.items()
            ])
            cols_order = [c for c in ["장소코드", "태그", "시설유형", "확인자", "확인시각",
                                      "출처", "등록근거"] if c in tag_view.columns]
            st.dataframe(tag_view[cols_order], use_container_width=True)

            del_target = st.selectbox(
                "삭제할 태그", list(st.session_state.location_tags.keys()), key="del_target"
            )
            if st.button("선택한 태그 삭제"):
                st.session_state.location_tags = A.delete_tag(
                    st.session_state.location_tags, del_target, path=TAG_PATH
                )
                st.success(f"{del_target} 태그를 삭제했습니다.")
                st.rerun()

    with tabs[4]:
        st.markdown("**재발가속 지점**")
        if len(accel):
            st.dataframe(accel, use_container_width=True)
        else:
            st.caption("탐지된 재발가속 지점이 없습니다.")
        st.markdown("**맞춤형 순찰 추천** (트랙='맞춤형 순찰'만 대상, 시설대응·업무통계·확인대기 제외)")
        st.dataframe(patrol, use_container_width=True)
        st.markdown("**시설대응/협업 트랙** (경찰관이 시설거점으로 확인한 지점)")
        facility_track = tracks[tracks["트랙"] == "시설대응/협업"]
        if len(facility_track):
            st.dataframe(facility_track[[A.COL_BASE, "건수", "주요유형", "시설유형", "원천"]],
                        use_container_width=True)
        else:
            st.caption("아직 시설거점으로 확인된 지점이 없습니다.")

    with tabs[5]:
        top_k = st.slider("전반기 상위 지점 수", 5, 50, 20, step=5)
        val = A.split_validation(conc_pool, top_k=top_k)
        metric_cards([
            ("적중률", f"{val['hit_rate']*100:.0f}%", "전반기 상위→후반기 반복", NAVY),
            ("포괄률", f"{val['coverage']*100:.1f}%", "후반기 반복신고 중 비중", AMBER),
            ("무작위 기대치", f"{val['random_expect']*100:.1f}%", "비교 기준선", "#9AA5B4"),
        ])
        merged = val["top_first_table"].rename("전반기").to_frame()
        merged["후반기"] = val["second_counts"]
        st.dataframe(merged, use_container_width=True)

    with tabs[6]:
        st.markdown("**Power Few TOP 20 상세** (트랙·판정사유 포함)")
        top20 = tracks.head(20)
        sel = st.selectbox("장소 선택", top20[A.COL_BASE].tolist(), key="top20_sel")
        row = top20[top20[A.COL_BASE] == sel].iloc[0]
        st.markdown(badge(row["트랙"], BADGE_CLS.get(row["트랙"], "b-review")), unsafe_allow_html=True)
        st.write({
            "건수": int(row["건수"]), "주요유형": row["주요유형"],
            "판정사유": row["판정사유"], "원천": row["원천"],
            "시설유형": row["시설유형"], "개입검토": row["개입검토"],
        })
        st.dataframe(
            top20[[A.COL_BASE, "건수", "주요유형", "트랙", "판정사유", "원천", "시설유형", "개입검토"]],
            use_container_width=True,
        )

    with tabs[7]:
        st.markdown("**Power Few Map** · 실제 주소·좌표는 사용하지 않는 개략도입니다 "
                    "(행정동 구역 + 지점 격자배치).")
        filter_key = st.radio("필터", MV.FILTER_OPTIONS, horizontal=True, key="map_filter")
        filtered_points = MV.apply_filter(map_points, filter_key)
        st.caption(f"표시 지점 {len(filtered_points):,}개 / 전체 {len(map_points):,}개")

        sel_options = filtered_points.sort_values("건수", ascending=False)[A.COL_BASE].tolist()
        map_sel = st.selectbox(
            "지점 선택 (지도에 강조 표시됩니다)", ["(선택 안함)"] + sel_options, key="map_select"
        )
        selected_base = None if map_sel == "(선택 안함)" else map_sel

        adapter = MV.SchematicAdapter()  # 외부 개발모드 기본값 — 실좌표 아님
        svg_html = MV.render_map_svg(filtered_points, adapter=adapter, selected_base=selected_base)
        st.markdown(svg_html, unsafe_allow_html=True)

        if selected_base:
            detail = MV.location_detail(selected_base, clean_df, map_points, patrol)
            if detail:
                st.markdown("---")
                st.markdown(badge(detail["트랙"], BADGE_CLS.get(detail["트랙"], "b-review")),
                           unsafe_allow_html=True)
                d1, d2, d3 = st.columns(3)
                d1.metric("신고건수", detail["신고건수"])
                d2.metric("평균 재발간격", f"{detail['평균재발간격_일']}일"
                         if detail["평균재발간격_일"] is not None else "—")
                d3.metric("주요시간대", detail["주요시간대"] or "—")
                st.write({
                    "행정동": detail["행정동"], "주요유형": detail["주요유형"],
                    "판정사유": detail["판정사유"], "원천": detail["원천"],
                    "시설유형": detail["시설유형"],
                    "추천행동": detail["추천행동"] or "(순찰 추천 대상 아님)",
                })

    with tabs[8]:
        st.markdown("**AI 어시스턴트 (오프라인)** · 외부 API·인터넷 연결 없이 동작합니다.")
        st.caption(
            "분석 결과를 물어보거나, 관할 지식을 알려주세요. 예: '오늘 야간 우선순찰 장소 "
            "알려줘' · '최근 가정폭력 재발가속 지점은?' · 'BASE00006은 구미차병원이야. "
            "시설거점-병원으로 기억해.'"
        )

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "pending_teach" not in st.session_state:
            st.session_state.pending_teach = None

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["text"])

        if st.session_state.pending_teach:
            p = st.session_state.pending_teach
            with st.chat_message("assistant"):
                fac = f" · {p['facility_type']}" if p.get("facility_type") else ""
                st.markdown(
                    f"이렇게 이해했습니다 — **{p['base_id']}** → **{p['tag']}**{fac}\n\n"
                    "저장할까요? 저장 전까지는 분석에 반영되지 않습니다."
                )
                cc1, cc2 = st.columns(2)
                if cc1.button("✅ 확인 (저장)", key="teach_confirm"):
                    st.session_state.location_tags = A.upsert_tag(
                        st.session_state.location_tags, p["base_id"], p["tag"],
                        facility_type=p.get("facility_type"), confirmer="AI 어시스턴트 대화",
                        ts=datetime.now().strftime("%m/%d %H:%M"), path=TAG_PATH,
                        source="assistant_chat", reason_text=p["raw_text"],
                    )
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "text": f"저장했습니다: {p['base_id']} → {p['tag']}{fac}",
                    })
                    st.session_state.pending_teach = None
                    st.rerun()
                if cc2.button("❌ 취소", key="teach_cancel"):
                    st.session_state.chat_history.append(
                        {"role": "assistant", "text": "저장을 취소했습니다."}
                    )
                    st.session_state.pending_teach = None
                    st.rerun()

        user_msg = st.chat_input("메시지를 입력하세요")
        if user_msg:
            st.session_state.chat_history.append({"role": "user", "text": user_msg})
            known_ids = set(tracks[A.COL_BASE])
            candidate = AS.DEFAULT_ENGINE.parse_teach(user_msg, known_ids)
            if candidate:
                st.session_state.pending_teach = candidate
                fac = f"({candidate['facility_type']})" if candidate.get("facility_type") else ""
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "text": (f"'{candidate['base_id']}'를 '{candidate['tag']}'{fac}로 "
                            "기억할까요? 아래에서 확인해주세요."),
                })
            else:
                ctx = {"tracks": tracks, "patrol": patrol, "accel": accel,
                      "facility_suspects": facility_suspects}
                answer = AS.DEFAULT_ENGINE.answer_query(user_msg, ctx)
                st.session_state.chat_history.append(
                    {"role": "assistant", "text": answer or AS.HELP_TEXT}
                )
            st.rerun()


def render_briefing():
    now = datetime.now().strftime("%H:%M")
    st.markdown(
        f"""<div style="display:flex;justify-content:space-between;align-items:center;
        background:#fff;border-radius:12px;padding:14px 18px;margin-bottom:14px;border:1px solid var(--border-c)">
        <span style="font-size:1.05rem;font-weight:700;color:var(--ink)">AI 교대 브리핑</span>
        <span style="font-size:.85rem;color:var(--slate)">{now} 기준 자동생성 · 리핏112</span></div>""",
        unsafe_allow_html=True,
    )

    st.markdown('<p class="rp-note" style="font-size:.8rem;letter-spacing:.04em">오늘 우선 확인 지점 TOP 3</p>',
               unsafe_allow_html=True)
    st.markdown(MV.render_briefing_map_svg(top3), unsafe_allow_html=True)
    cols = st.columns(3)
    for col, card in zip(cols, top3 + [None] * (3 - len(top3))):
        with col:
            if card is None:
                st.markdown('<div class="headline-card hc-normal">데이터 부족</div>', unsafe_allow_html=True)
                continue
            cls = "hc-urgent" if card["사유"] == "인계메모 긴급" else (
                "hc-accel" if card["사유"] == "재발가속" else "hc-normal")
            tagcolor = RISK if cls == "hc-urgent" else (AMBER if cls == "hc-accel" else NAVY)
            st.markdown(
                f"""<div class="headline-card {cls}">
                <span class="brief-tag" style="background:{tagcolor}">{card['사유']}</span>
                <p style="font-family:var(--font-mono);font-size:1.2rem;font-weight:700;margin:8px 0 4px">{card['장소코드']}</p>
                <p style="font-size:.85rem;margin:0 0 8px">{card['요약']}</p>
                <p style="font-size:.82rem;font-weight:700;margin:0">▶ {card['추천행동']}</p>
                <p style="font-size:.72rem;color:var(--slate);margin:6px 0 0">{card['출처']}</p>
                </div>""", unsafe_allow_html=True,
            )

    st.markdown('<p class="rp-note" style="font-size:.8rem;letter-spacing:.04em;margin-top:18px">근거 패널</p>',
               unsafe_allow_html=True)
    n_accel = len(accel)
    n_admin_excluded = len(clean_df) - len(conc_pool)
    n_facility_confirmed = (tracks["트랙"] == "시설대응/협업").sum()
    n_pending = (tracks["트랙"] == "확인대기").sum()
    metric_cards([
        ("Power Few 스냅샷", f"상위1% {conc_adj['top1']['share']*100:.0f}%", f"반복장소 {conc_adj['n_places']:,}곳", NAVY),
        ("재발가속 장소", f"{n_accel}곳", "간격이 짧아진 지점", AMBER),
        ("시설대응 확인", f"{n_facility_confirmed}곳", "경찰관 확인된 시설거점", CALM),
        ("확인대기", f"{n_pending}곳", "시설의심 등 검토 필요", "#9AA5B4"),
    ])
    st.markdown(
        f'<p class="rp-note">행정접수·확정된 업무통계 트랙 자동 제외 {n_admin_excluded:,}건 '
        "(세부 내역은 일반 대시보드에서 확인)</p>", unsafe_allow_html=True,
    )

    st.markdown('<p class="rp-note" style="font-size:.8rem;letter-spacing:.04em;margin-top:10px">전 근무자 인계사항 · 사람이 직접 작성</p>',
               unsafe_allow_html=True)
    for n in reversed(st.session_state.handoff_notes):
        urgent_tag = badge("긴급", "b-review") if n.get("긴급") else ""
        st.markdown(
            f"""<div class="note-row"><i class="ti ti-pencil"></i>
            <div style="flex:1"><b>{n.get('장소코드') or '(장소 미지정)'}</b> · {n['내용']}
            <div style="font-size:.72rem;color:var(--slate)">{n['작성자']} · {n['작성시각']}</div></div>
            {urgent_tag}</div>""", unsafe_allow_html=True,
        )
    if not st.session_state.handoff_notes:
        st.caption("등록된 인계사항이 없습니다.")

    with st.form("handoff_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        loc = c1.text_input("관련 장소코드 (선택)")
        writer = c2.text_input("작성자")
        urgent = c3.checkbox("긴급")
        content = st.text_area("다음 근무조에게 남길 인계사항")
        if st.form_submit_button("인계사항 등록") and content.strip():
            st.session_state.handoff_notes.append({
                "장소코드": loc.strip() or None, "내용": content.strip(),
                "작성자": writer.strip() or "미상", "작성시각": datetime.now().strftime("%H:%M"),
                "긴급": urgent,
            })
            st.rerun()


with st.sidebar:
    st.markdown("---")
    mode = st.radio("화면 모드", ["일반 대시보드", "교대 브리핑 모드"], index=0)
    if len(surge_suspects):
        with st.expander(f"⚠ 제도변화 의심 {len(surge_suspects)}건"):
            for _, r in surge_suspects.iterrows():
                checked = st.checkbox(
                    f"{r['사건종별']} ({r['과거비중_평균']}%→{r['최근비중_평균']}%)",
                    value=r["사건종별"] in st.session_state.confirmed_surge_types,
                    key=f"surge_{r['사건종별']}",
                )
                name = r["사건종별"]
                if checked and name not in st.session_state.confirmed_surge_types:
                    st.session_state.confirmed_surge_types.append(name)
                elif not checked and name in st.session_state.confirmed_surge_types:
                    st.session_state.confirmed_surge_types.remove(name)

if mode == "일반 대시보드":
    render_dashboard()
else:
    render_briefing()
