# -*- coding: utf-8 -*-
"""RE:PEAT 112 — 완전 재작성 버전"""
from datetime import datetime
import os, pandas as pd, streamlit as st
import analysis as A, assistant as AS, map_view as MV

# 샘플 데이터 자동 생성
if not os.path.exists("sample_v3_data.csv"):
    import generate_sample_v3
    generate_sample_v3.make_data().to_csv("sample_v3_data.csv", index=False, encoding="utf-8-sig")

st.set_page_config(page_title="RE:PEAT 112", page_icon="🚔", layout="wide", initial_sidebar_state="collapsed")

# ── 디자인 토큰 ──────────────────────────────────────────────
NAVY="#12203D"; AMBER="#D97706"; RISK="#DC2626"; CALM="#16A34A"

st.markdown("""<style>
:root{--bg:#F5F6FA;--card:#fff;--border:#E8EAF0;--blue:#1B4FBB;--blue-l:#EBF0FB;
--red:#DC2626;--red-l:#FEF2F2;--amber:#D97706;--amb-l:#FFFBEB;
--green:#16A34A;--grn-l:#F0FDF4;--ink:#1A1D23;--sub:#4B5563;--muted:#9CA3AF;
--mono:ui-monospace,monospace;--r:10px;
--shadow:0 1px 3px rgba(0,0,0,.08);}
html,body,[class*=css]{font-family:-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;}
.stApp{background:var(--bg)!important;}
section[data-testid=stSidebar]{background:var(--card)!important;border-right:1px solid var(--border)!important;}
#MainMenu,footer,header,[data-testid=stToolbar],[data-testid=stDecoration]{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
/* 앱바 */
.topbar{background:var(--card);border-bottom:2px solid var(--blue);
  display:flex;align-items:center;padding:0 32px;height:54px;
  position:sticky;top:0;z-index:999;box-shadow:0 2px 8px rgba(0,0,0,.08);}
.topbar-logo{display:flex;align-items:center;gap:10px;
  padding-right:24px;border-right:1px solid var(--border);margin-right:20px;}
.topbar-logo-icon{width:32px;height:32px;border-radius:8px;background:var(--blue);
  color:#fff;font-weight:900;font-size:.75rem;display:flex;align-items:center;justify-content:center;}
.topbar-logo-text .t1{font-weight:700;color:var(--ink);font-size:.88rem;display:block;line-height:1.3;}
.topbar-logo-text .t2{font-size:.7rem;color:var(--muted);display:block;}
.topbar-right{margin-left:auto;font-size:.76rem;color:var(--muted);}
.topbar-badge{background:var(--blue-l);color:var(--blue);font-size:.7rem;
  font-weight:700;padding:3px 10px;border-radius:20px;margin-right:10px;}
/* 메인 */
.main{padding:28px 40px 48px;max-width:1380px;margin:0 auto;}
/* KPI */
.kpi-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:24px;}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:22px 24px;box-shadow:var(--shadow);display:flex;align-items:flex-start;justify-content:space-between;}
.kpi-left .lbl{font-size:.72rem;color:var(--muted);font-weight:500;margin-bottom:8px;display:block;}
.kpi-left .val{font-family:var(--mono);font-size:2rem;font-weight:700;line-height:1;margin-bottom:5px;display:block;}
.kpi-left .sub{font-size:.71rem;color:var(--muted);display:block;}
.kpi-icon{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0;}
.kpi-blue .val{color:var(--blue);} .kpi-blue .kpi-icon{background:var(--blue-l);}
.kpi-red .val{color:var(--red);} .kpi-red .kpi-icon{background:var(--red-l);}
.kpi-amber .val{color:var(--amber);} .kpi-amber .kpi-icon{background:var(--amb-l);}
.kpi-green .val{color:var(--green);} .kpi-green .kpi-icon{background:var(--grn-l);}
.kpi-gray .val{color:var(--sub);} .kpi-gray .kpi-icon{background:#F3F4F6;}
/* 섹션 */
.sec{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  box-shadow:var(--shadow);overflow:hidden;margin-bottom:20px;}
.sec-head{display:flex;align-items:center;justify-content:space-between;
  padding:16px 22px;border-bottom:1px solid var(--border);}
.sec-title{font-size:.9rem;font-weight:700;color:var(--ink);margin:0;display:flex;align-items:center;gap:8px;}
.sec-badge{background:var(--blue-l);color:var(--blue);font-size:.68rem;font-weight:700;padding:2px 9px;border-radius:20px;}
.sec-body{padding:20px 22px;}
.sec-link{font-size:.76rem;color:var(--blue);}
/* 순찰 카드 */
.patrol-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.pc{border:1px solid var(--border);border-radius:var(--r);overflow:hidden;background:var(--card);}
.pc-top{padding:14px 18px 12px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px;}
.pc-rank{width:24px;height:24px;border-radius:50%;background:var(--blue);color:#fff;
  font-family:var(--mono);font-size:.72rem;font-weight:700;
  display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.pc.urgent .pc-rank{background:var(--red);}
.pc-id{font-family:var(--mono);font-size:.9rem;font-weight:700;color:var(--ink);}
.pc-type{font-size:.71rem;background:#F3F4F6;color:var(--sub);border-radius:5px;padding:2px 8px;white-space:nowrap;}
.pc-body{padding:14px 18px;}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;}
.chip{font-size:.7rem;padding:3px 9px;border-radius:20px;background:#F3F4F6;color:var(--sub);border:1px solid var(--border);}
.chip.b{background:var(--blue-l);color:var(--blue);border-color:#BFD1F6;}
.chip.r{background:var(--red-l);color:var(--red);border-color:#FECACA;}
.chip.a{background:var(--amb-l);color:var(--amber);border-color:#FDE68A;}
.pc-action{font-size:.8rem;font-weight:700;color:var(--blue);}
.pc.urgent .pc-action{color:var(--red);}
/* 요약 리스트 */
.sum-row{display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);font-size:.82rem;}
.sum-row:last-child{border-bottom:none;}
.dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:5px;}
.dr{background:var(--red);} .da{background:var(--amber);} .db{background:var(--blue);} .dg{background:#D1D5DB;}
.sum-text{flex:1;line-height:1.5;color:var(--sub);}
.sum-text b{color:var(--ink);}
/* 분포 바 */
.bar-row{display:flex;align-items:center;gap:12px;margin-bottom:10px;}
.bar-lbl{font-size:.78rem;color:var(--sub);width:60px;flex-shrink:0;}
.bar-track{flex:1;height:9px;background:#F3F4F6;border-radius:5px;overflow:hidden;}
.bar-fill{height:100%;border-radius:5px;}
.bar-val{font-size:.75rem;color:var(--muted);width:36px;text-align:right;flex-shrink:0;font-family:var(--mono);}
/* Power Few */
.pf-row{display:flex;align-items:baseline;gap:10px;margin-bottom:12px;}
.pf-pct{font-family:var(--mono);font-size:1.7rem;font-weight:800;color:var(--blue);}
.pf-desc{font-size:.82rem;color:var(--muted);}
/* AI판정 */
.jg{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.ji{border:1px solid var(--border);border-radius:var(--r);padding:14px 16px;background:var(--card);}
.ji .jl{font-size:.72rem;color:var(--muted);margin-bottom:5px;}
.ji .jv{font-family:var(--mono);font-size:1.3rem;font-weight:700;color:var(--ink);}
.ji .js{font-size:.7rem;color:var(--muted);margin-top:2px;}
.ji.jr{border-left:3px solid var(--red);} .ji.jb{border-left:3px solid var(--blue);}
.ji.ja{border-left:3px solid var(--amber);} .ji.jg2{border-left:3px solid #D1D5DB;}
/* 브리핑 */
.hc{border-radius:var(--r);padding:18px 20px;}
.hc-u{background:var(--red-l);border:1px solid #FECACA;}
.hc-a{background:var(--amb-l);border:1px solid #FDE68A;}
.hc-n{background:var(--blue-l);border:1px solid #BFD1F6;}
.brief-tag{font-family:var(--mono);font-size:.68rem;padding:2px 8px;border-radius:5px;color:#fff;display:inline-block;margin-bottom:8px;}
/* 공용 */
.badge{display:inline-block;font-size:.74rem;padding:3px 10px;border-radius:5px;margin:2px 3px 2px 0;}
.b-real{background:var(--blue-l);color:var(--blue);} .b-accel{background:var(--red-l);color:var(--red);}
.b-admin{background:#F9FAFB;color:var(--muted);} .b-inst{background:#F5F3FF;color:#6D28D9;}
.b-review{background:#F9FAFB;color:var(--muted);} .b-region{background:var(--grn-l);color:var(--green);}
.note-row{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);font-size:.83rem;}
[data-testid=stDataFrame]{border:1px solid var(--border)!important;border-radius:var(--r)!important;}
</style>""", unsafe_allow_html=True)

# ── 헬퍼 ─────────────────────────────────────────────────────
def badge(t,c): return f'<span class="badge {c}">{t}</span>'
def metric_cards(items):
    cells="".join(f'<div style="background:#fff;border:1px solid #E8EAF0;border-left:4px solid {c};border-radius:10px;padding:16px 18px"><div style="font-size:.72rem;color:#9CA3AF;margin-bottom:6px">{l}</div><div style="font-family:ui-monospace,monospace;font-size:1.5rem;font-weight:700;color:#1A1D23">{v}</div><div style="font-size:.7rem;color:#9CA3AF;margin-top:4px">{cap}</div></div>' for l,v,cap,c in items)
    st.markdown(f'<div style="display:grid;gap:14px;margin:8px 0 18px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">{cells}</div>',unsafe_allow_html=True)
BADGE_CLS={"실제 반복수요":"b-real","재발가속":"b-accel","지역분산 신호":"b-region","행정접수 아티팩트":"b-admin","제도관리형":"b-inst","검토필요":"b-review","시설의심(확인대기)":"b-region","맞춤형 순찰":"b-real","시설대응/협업":"b-inst","업무량 통계":"b-admin","확인대기":"b-review"}

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("**📂 데이터**")
    uploaded = st.file_uploader("CSV / Excel 업로드", type=["csv","xlsx"], label_visibility="collapsed")
    use_sample = st.checkbox("샘플 데이터로 시연", value=uploaded is None)
    st.markdown("---")
    mode = st.radio("화면", ["대시보드","교대 브리핑"], index=0, label_visibility="collapsed")
    st.caption("🔒 비식별 자료만 사용")

# ── 데이터 로드 ───────────────────────────────────────────────
@st.cache_data
def load_sample(): return pd.read_csv("sample_v3_data.csv")
def load_up(f):
    if f.name.endswith(".xlsx"):
        try: return pd.read_excel(f, sheet_name="분석데이터")
        except: return pd.read_excel(f)
    return pd.read_csv(f)

if uploaded: raw, src = load_up(uploaded), f"업로드({uploaded.name})"
elif use_sample: raw, src = load_sample(), "샘플 데이터(가상)"
else:
    st.info("좌측에서 데이터를 선택하세요."); st.stop()

diag = A.diagnose(raw)
if diag["missing_columns"]: st.error(f"필수 컬럼 없음: {diag['missing_columns']}"); st.stop()

@st.cache_data(show_spinner=False)
def _clean(df): return A.clean(df)
@st.cache_data(show_spinner=False)
def _detect(clean_df):
    return A.detect_admin_artifacts(clean_df), A.detect_institutional_surge(clean_df), A.detect_facility_suspects(clean_df)

clean_df, clean_log = _clean(raw)
artifacts, surge_suspects, facility_suspects = _detect(clean_df)

# 세션 초기화
for k,v in [("confirmed_surge_types",[]),("location_tags",A.load_tags()),("handoff_notes",[]),("chat_history",[]),("pending_teach",None)]:
    if k not in st.session_state: st.session_state[k]=v
st.session_state.confirmed_surge_types = [t for t in st.session_state.confirmed_surge_types if t in surge_suspects["사건종별"].tolist()]

confirmed = st.session_state.confirmed_surge_types
corrected = A.apply_corrections(clean_df, artifacts, confirmed)
conc_raw = A.concentration(clean_df)
accel = A.detect_acceleration(corrected)
tracks = A.classify_tracks(clean_df, artifacts, confirmed, facility_suspects, accel, st.session_state.location_tags)
conc_pool_bases = set(tracks[tracks["트랙"].isin(["맞춤형 순찰","확인대기"])][A.COL_BASE])
conc_pool = clean_df[clean_df[A.COL_BASE].isin(conc_pool_bases)]
conc_adj = A.concentration(conc_pool)
patrol = A.recommend_patrol(clean_df, tracks, accel, top_n=15)
map_points = MV.attach_dong(tracks, clean_df)
top3 = A.build_top3(patrol, st.session_state.handoff_notes, top_n=3)
TAG_PATH = A.DEFAULT_TAG_FILE
now_str = datetime.now().strftime("%Y.%m.%d %H:%M")

# ── 앱바 ─────────────────────────────────────────────────────
st.markdown(f"""<div class="topbar">
  <div class="topbar-logo">
    <div class="topbar-logo-icon">112</div>
    <div class="topbar-logo-text"><span class="t1">RE:PEAT 112</span><span class="t2">형곡지구대 · 반복신고 수요 분석</span></div>
  </div>
  <div class="topbar-right">
    <span class="topbar-badge">POWER FEW 분석</span>기준일시 {now_str}
  </div>
</div>""", unsafe_allow_html=True)

# ── 탭 (Streamlit 기본 — 최상단에 한 번만) ───────────────────
if mode == "대시보드":
    tabs = st.tabs(["🏠 홈","📊 분석","🚔 순찰추천","🗺 지도","🔍 거점확인","🤖 Assistant"])

    # ── 홈 탭 ─────────────────────────────────────────────────
    with tabs[0]:
        n_total = clean_log["final_rows"]
        n_accel = len(accel)
        n_patrol = int((tracks["트랙"]=="맞춤형 순찰").sum())
        n_pend = int((tracks["트랙"]=="확인대기").sum())
        n_excl = len(clean_df)-len(conc_pool)
        pf5 = conc_adj["top5"]["share"]*100

        st.markdown('<div class="main">', unsafe_allow_html=True)

        # 페이지 헤더
        st.markdown(f"""<div style="margin-bottom:22px">
          <p style="font-size:1.2rem;font-weight:700;color:#1A1D23;margin:0 0 4px">공공 치안 AI 분석 현황</p>
          <p style="font-size:.76rem;color:#9CA3AF;margin:0">반복신고 수요 진단 및 개입 우선순위 · Power Few 기반 · {now_str} 자동생성</p>
        </div>""", unsafe_allow_html=True)

        # KPI 5개
        st.markdown(f"""<div class="kpi-grid">
          <div class="kpi kpi-blue"><div class="kpi-left"><span class="lbl">전체 신고건수</span><span class="val">{n_total:,}</span><span class="sub">분석 대상 기간 전체</span></div><div class="kpi-icon">📋</div></div>
          <div class="kpi kpi-red"><div class="kpi-left"><span class="lbl">재발가속 지점</span><span class="val">{n_accel}</span><span class="sub">재신고 간격이 짧아진 곳</span></div><div class="kpi-icon">⚠️</div></div>
          <div class="kpi kpi-amber"><div class="kpi-left"><span class="lbl">Power Few 상위 5%</span><span class="val">{pf5:.0f}%</span><span class="sub">{conc_adj["top5"]["k_places"]}곳 → 전체의 {pf5:.0f}%</span></div><div class="kpi-icon">📊</div></div>
          <div class="kpi kpi-green"><div class="kpi-left"><span class="lbl">맞춤형 순찰 지점</span><span class="val">{n_patrol}</span><span class="sub">오늘 순찰 추천 대상</span></div><div class="kpi-icon">🚔</div></div>
          <div class="kpi kpi-gray"><div class="kpi-left"><span class="lbl">확인대기 지점</span><span class="val">{n_pend}</span><span class="sub">거점 유형 미확인 / 제외 {n_excl}건</span></div><div class="kpi-icon">🔍</div></div>
        </div>""", unsafe_allow_html=True)

        # 2행: 순찰 TOP3 + 상황요약
        c1, c2 = st.columns([2, 1])
        with c1:
            cards_html = ""
            for i,(_, row) in enumerate(patrol.head(3).iterrows(), 1):
                is_u = pd.notna(row["가속배율"]) and row["가속배율"]<0.7
                cls = "pc urgent" if is_u else "pc"
                ac = f'<span class="chip r">가속 {row["가속배율"]:.2f}</span>' if is_u else ""
                cards_html += f"""<div class="{cls}">
                  <div class="pc-top"><div class="pc-rank">{i}</div>
                  <div class="pc-id">{row[A.COL_BASE]}</div>
                  <div class="pc-type">{row["주요유형"]}</div></div>
                  <div class="pc-body">
                    <div class="chips"><span class="chip b">{row["추천순찰시간대"]}</span><span class="chip">{int(row["건수"])}건</span>{ac}</div>
                    <div class="pc-action">▶ {row["추천행동"]}</div>
                  </div></div>"""
            st.markdown(f"""<div class="sec">
              <div class="sec-head"><p class="sec-title">오늘의 맞춤형 순찰 TOP3 <span class="sec-badge">Power Few 기반</span></p><span class="sec-link">전체 보기 →</span></div>
              <div class="sec-body"><div class="patrol-grid">{cards_html}</div></div>
            </div>""", unsafe_allow_html=True)

        with c2:
            n_fac = int((tracks["트랙"]=="시설대응/협업").sum())
            n_adm = int((tracks["트랙"]=="업무량 통계").sum())
            rows=""
            for _,r in accel.head(3).iterrows():
                rows+=f'<div class="sum-row"><div class="dot dr"></div><div class="sum-text"><b>{r[A.COL_BASE]}</b> 재발가속 — 재신고 간격 {r["최근평균간격_일"]}일</div></div>'
            rows+=f'<div class="sum-row"><div class="dot da"></div><div class="sum-text"><b>확인대기</b> {n_pend}곳 — 거점 유형 미확인</div></div>'
            rows+=f'<div class="sum-row"><div class="dot db"></div><div class="sum-text"><b>시설거점</b> {n_fac}곳 확인 / 행정접수 {n_adm}곳 분리</div></div>'
            rows+=f'<div class="sum-row"><div class="dot dg"></div><div class="sum-text">지니계수 <b>{conc_adj["gini"]:.3f}</b> — 소수 지점 집중 강도</div></div>'
            st.markdown(f"""<div class="sec" style="height:100%">
              <div class="sec-head"><p class="sec-title">핵심 상황 요약</p></div>
              <div class="sec-body">{rows}</div>
            </div>""", unsafe_allow_html=True)

        # 3행: 지도 + 집중도
        c3, c4 = st.columns([3, 2])
        with c3:
            fmap = MV.apply_filter(map_points, "Power Few")
            svg = MV.render_map_svg(fmap, adapter=MV.SchematicAdapter(), height=260)
            st.markdown(f'<div class="sec"><div class="sec-head"><p class="sec-title">Power Few Map <span class="sec-badge">행정동 개략도 · 실좌표 아님</span></p></div><div class="sec-body">{svg}</div></div>', unsafe_allow_html=True)
        with c4:
            pf_rows=""
            for p in (1,5,10):
                sh=conc_adj[f"top{p}"]["share"]*100; k=conc_adj[f"top{p}"]["k_places"]
                pf_rows+=f'<div class="pf-row"><div class="pf-pct">{sh:.1f}%</div><div class="pf-desc">상위 {p}% ({k}곳)</div></div>'
            st.markdown(f'<div class="sec"><div class="sec-head"><p class="sec-title">Power Few 집중도 <span class="sec-badge">지니 {conc_adj["gini"]:.3f}</span></p></div><div class="sec-body">{pf_rows}</div></div>', unsafe_allow_html=True)

        # 4행: 사건유형 + 시간대 + AI판정
        c5, c6, c7 = st.columns(3)
        with c5:
            td=clean_df["종별분류"].value_counts(); tot=td.sum()
            bars="".join(f'<div class="bar-row"><div class="bar-lbl">{k[:4]}</div><div class="bar-track"><div class="bar-fill" style="width:{v/tot*100:.0f}%;background:#1B4FBB"></div></div><div class="bar-val">{v/tot*100:.0f}%</div></div>' for k,v in td.head(5).items())
            st.markdown(f'<div class="sec"><div class="sec-head"><p class="sec-title">사건 유형 분포</p></div><div class="sec-body">{bars}</div></div>', unsafe_allow_html=True)
        with c6:
            tc={"주간":"#1B4FBB","저녁":"#D97706","야간":"#DC2626"}
            if "시간대구간" in clean_df.columns:
                td2=clean_df["시간대구간"].value_counts(); tot2=td2.sum()
                bars2="".join(f'<div class="bar-row"><div class="bar-lbl">{k}</div><div class="bar-track"><div class="bar-fill" style="width:{v/tot2*100:.0f}%;background:{tc.get(k,"#6B7280")}"></div></div><div class="bar-val">{v/tot2*100:.0f}%</div></div>' for k,v in td2.items())
            else: bars2="<p style='font-size:.78rem;color:#9CA3AF'>시간대 데이터 없음</p>"
            st.markdown(f'<div class="sec"><div class="sec-head"><p class="sec-title">시간대별 신고 분포</p></div><div class="sec-body">{bars2}</div></div>', unsafe_allow_html=True)
        with c7:
            n_r=int((tracks["트랙"]=="맞춤형 순찰").sum()); n_f=int((tracks["트랙"]=="시설대응/협업").sum())
            n_s=int((tracks["트랙"]=="업무량 통계").sum()); n_w=int((tracks["트랙"]=="확인대기").sum())
            st.markdown(f"""<div class="sec"><div class="sec-head"><p class="sec-title">AI 거점 판정 요약</p></div><div class="sec-body"><div class="jg">
              <div class="ji jr"><div class="jl">맞춤형 순찰</div><div class="jv">{n_r}</div><div class="js">진짜 반복지점</div></div>
              <div class="ji ja"><div class="jl">확인대기</div><div class="jv">{n_w}</div><div class="js">시설의심 등</div></div>
              <div class="ji jb"><div class="jl">시설대응/협업</div><div class="jv">{n_f}</div><div class="js">경찰관 확인됨</div></div>
              <div class="ji jg2"><div class="jl">업무량 통계</div><div class="jv">{n_s}</div><div class="js">행정접수 거점</div></div>
            </div></div></div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── 분석 탭 ──────────────────────────────────────────────
    with tabs[1]:
        st.markdown('<div style="padding:24px 32px">', unsafe_allow_html=True)
        sub = st.selectbox("분석 항목 선택", ["품질진단","Power Few 집중도","시간분할 검증","TOP20 상세"])
        if sub=="품질진단":
            st.markdown("#### 데이터 품질 자동진단")
            metric_cards([("중복행",diag["duplicate_rows"],"완전 중복",RISK),("코드 오류",diag.get("code_anomalies",0),"C1선→C1",AMBER),("위치 결측",clean_log["removed_no_location"],"장소코드 없음",NAVY),("최종 분석건수",f"{clean_log['final_rows']:,}","",CALM)])
        elif sub=="Power Few 집중도":
            st.markdown("#### Power Few 집중도")
            view=st.radio("기준",["보정분석","원시분석"],horizontal=True)
            conc=conc_adj if view=="보정분석" else conc_raw
            metric_cards([(f"상위 {p}% ({conc[f'top{p}']['k_places']}곳)",f"{conc[f'top{p}']['share']*100:.1f}%","전체 신고 점유율","#1B4FBB") for p in (1,5,10)]+[("지니계수",f"{conc['gini']:.3f}","1에 가까울수록 집중",AMBER)])
            ldf=pd.DataFrame({"지점누적비율":conc["lorenz_x"],"신고누적비율":conc["lorenz_y"],"균등기준선":conc["lorenz_x"]}).set_index("지점누적비율")
            st.line_chart(ldf,height=280)
            if len(surge_suspects):
                st.markdown("**제도변화 의심 후보**")
                show=surge_suspects.copy(); show["상태"]=show["사건종별"].apply(lambda t:"✅ 확인됨" if t in confirmed else "⚠ 미확인")
                st.dataframe(show,use_container_width=True)
        elif sub=="시간분할 검증":
            st.markdown("#### 시간분할 검증")
            top_k=st.slider("상위 지점 수",5,50,20,step=5)
            val=A.split_validation(conc_pool,top_k=top_k)
            metric_cards([("적중률",f"{val['hit_rate']*100:.0f}%","전반기→후반기","#1B4FBB"),("포괄률",f"{val['coverage']*100:.1f}%","후반기 반복 중 비중",AMBER),("무작위 기대치",f"{val['random_expect']*100:.1f}%","비교 기준선","#9CA3AF")])
            merged=val["top_first_table"].rename("전반기").to_frame(); merged["후반기"]=val["second_counts"]
            st.dataframe(merged,use_container_width=True)
        elif sub=="TOP20 상세":
            st.markdown("#### Power Few TOP20")
            top20=tracks.head(20)
            sel=st.selectbox("장소 선택",top20[A.COL_BASE].tolist())
            row=top20[top20[A.COL_BASE]==sel].iloc[0]
            st.markdown(badge(row["트랙"],BADGE_CLS.get(row["트랙"],"b-review")),unsafe_allow_html=True)
            st.write({"건수":int(row["건수"]),"주요유형":row["주요유형"],"판정사유":row["판정사유"],"추천행동":row.get("추천행동","—")})
            st.dataframe(top20[[A.COL_BASE,"건수","주요유형","트랙","판정사유","원천"]],use_container_width=True)
        st.markdown('</div>',unsafe_allow_html=True)

    # ── 순찰추천 탭 ───────────────────────────────────────────
    with tabs[2]:
        st.markdown('<div style="padding:24px 32px">', unsafe_allow_html=True)
        st.markdown("#### 맞춤형 순찰 추천")
        if len(accel):
            st.markdown("**재발가속 지점**"); st.dataframe(accel,use_container_width=True)
        st.markdown("**순찰 추천 목록**"); st.dataframe(patrol,use_container_width=True)
        st.markdown('</div>',unsafe_allow_html=True)

    # ── 지도 탭 ──────────────────────────────────────────────
    with tabs[3]:
        st.markdown('<div style="padding:24px 32px">', unsafe_allow_html=True)
        st.markdown("#### Power Few Map · 행정동 개략도 (실좌표 아님)")
        fk=st.radio("필터",MV.FILTER_OPTIONS,horizontal=True)
        fp=MV.apply_filter(map_points,fk)
        st.caption(f"표시 {len(fp):,}개 / 전체 {len(map_points):,}개")
        sel2=st.selectbox("지점 선택",["(없음)"]+fp.sort_values("건수",ascending=False)[A.COL_BASE].tolist())
        sb=None if sel2=="(없음)" else sel2
        st.markdown(MV.render_map_svg(fp,adapter=MV.SchematicAdapter(),selected_base=sb,height=420),unsafe_allow_html=True)
        if sb:
            det=MV.location_detail(sb,clean_df,map_points,patrol)
            if det:
                d1,d2,d3=st.columns(3)
                d1.metric("신고건수",det["신고건수"]); d2.metric("평균 재발간격",f"{det['평균재발간격_일']}일" if det["평균재발간격_일"] else "—"); d3.metric("주요시간대",det["주요시간대"] or "—")
                st.write({"행정동":det["행정동"],"주요유형":det["주요유형"],"트랙":det["트랙"],"추천행동":det["추천행동"] or "해당없음"})
        st.markdown('</div>',unsafe_allow_html=True)

    # ── 거점확인 탭 ──────────────────────────────────────────
    with tabs[4]:
        st.markdown('<div style="padding:24px 32px">', unsafe_allow_html=True)
        st.markdown("#### 거점 유형 확인 · AI 후보 제시 → 경찰관 확인 → 태그 저장")
        tc=tracks["트랙"].value_counts()
        chips="".join(badge(f"{k} · {v}곳",BADGE_CLS.get(k,"b-review")) for k,v in tc.items())
        st.markdown(chips,unsafe_allow_html=True)
        st.markdown("---")
        if len(facility_suspects):
            st.markdown("**시설의심 후보 TOP10**"); st.dataframe(facility_suspects.head(10),use_container_width=True)
        st.markdown("**태그 등록**")
        c_a,c_b=st.columns([2,1])
        tgt=c_a.selectbox("장소 선택",tracks.sort_values("건수",ascending=False)[A.COL_BASE].tolist(),key="tg")
        ex=st.session_state.location_tags.get(tgt)
        cur_row=tracks[tracks[A.COL_BASE]==tgt].iloc[0]
        c_b.markdown(badge(cur_row["트랙"],BADGE_CLS.get(cur_row["트랙"],"b-review")),unsafe_allow_html=True)
        tc2=st.radio("태그",A.TAG_OPTIONS,index=A.TAG_OPTIONS.index(ex["태그"]) if ex else 3,horizontal=True,key="tc2")
        ft=None
        if tc2=="시설거점":
            fd=ex.get("시설유형",A.FACILITY_SUBTYPES[0]) if ex else A.FACILITY_SUBTYPES[0]
            ft=st.selectbox("시설유형",A.FACILITY_SUBTYPES,index=A.FACILITY_SUBTYPES.index(fd) if fd in A.FACILITY_SUBTYPES else 0)
        cf=st.text_input("확인자",value=ex.get("확인자","") if ex else "")
        if st.button("태그 저장"):
            st.session_state.location_tags=A.upsert_tag(st.session_state.location_tags,tgt,tc2,facility_type=ft,confirmer=cf.strip() or "미상",ts=datetime.now().strftime("%m/%d %H:%M"),path=TAG_PATH)
            st.success(f"{tgt} → '{tc2}' 저장 완료"); st.rerun()
        if st.session_state.location_tags:
            st.markdown("**저장된 태그 목록**")
            tv=pd.DataFrame([{"장소코드":k,**v} for k,v in st.session_state.location_tags.items()])
            cols=[c for c in ["장소코드","태그","시설유형","확인자","확인시각","출처","등록근거"] if c in tv.columns]
            st.dataframe(tv[cols],use_container_width=True)
            dl=st.selectbox("삭제",list(st.session_state.location_tags.keys()),key="dl")
            if st.button("삭제"):
                st.session_state.location_tags=A.delete_tag(st.session_state.location_tags,dl,path=TAG_PATH)
                st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

    # ── Assistant 탭 ─────────────────────────────────────────
    with tabs[5]:
        st.markdown('<div style="padding:24px 32px">', unsafe_allow_html=True)
        st.markdown("#### AI 어시스턴트 (오프라인) · 외부 API 없이 동작")
        st.caption("질문: '야간 우선순찰 장소 알려줘' / 학습: 'BASE00006은 구미차병원이야. 시설거점-병원으로 기억해.'")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["text"])
        if st.session_state.pending_teach:
            p=st.session_state.pending_teach
            with st.chat_message("assistant"):
                ft2=f"({p['facility_type']})" if p.get("facility_type") else ""
                st.markdown(f"**{p['base_id']}** → **{p['tag']}**{ft2} 로 기억할까요?")
                cc1,cc2=st.columns(2)
                if cc1.button("✅ 확인 (저장)",key="tc"):
                    st.session_state.location_tags=A.upsert_tag(st.session_state.location_tags,p["base_id"],p["tag"],facility_type=p.get("facility_type"),confirmer="AI 대화",ts=datetime.now().strftime("%m/%d %H:%M"),path=TAG_PATH,source="assistant_chat",reason_text=p["raw_text"])
                    st.session_state.chat_history.append({"role":"assistant","text":f"저장했습니다: {p['base_id']} → {p['tag']}{ft2}"})
                    st.session_state.pending_teach=None; st.rerun()
                if cc2.button("❌ 취소",key="tcancel"):
                    st.session_state.chat_history.append({"role":"assistant","text":"취소했습니다."})
                    st.session_state.pending_teach=None; st.rerun()
        um=st.chat_input("메시지를 입력하세요")
        if um:
            st.session_state.chat_history.append({"role":"user","text":um})
            ki=set(tracks[A.COL_BASE])
            cand=AS.DEFAULT_ENGINE.parse_teach(um,ki)
            if cand:
                st.session_state.pending_teach=cand
                ft3=f"({cand['facility_type']})" if cand.get("facility_type") else ""
                st.session_state.chat_history.append({"role":"assistant","text":f"'{cand['base_id']}'를 '{cand['tag']}'{ft3}로 기억할까요? 아래에서 확인해주세요."})
            else:
                ctx={"tracks":tracks,"patrol":patrol,"accel":accel,"facility_suspects":facility_suspects}
                ans=AS.DEFAULT_ENGINE.answer_query(um,ctx)
                st.session_state.chat_history.append({"role":"assistant","text":ans or AS.HELP_TEXT})
            st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

# ── 교대 브리핑 모드 ──────────────────────────────────────────
else:
    now_str2=datetime.now().strftime("%H:%M")
    st.markdown(f"""<div class="topbar">
      <div class="topbar-logo">
        <div class="topbar-logo-icon">112</div>
        <div class="topbar-logo-text"><span class="t1">AI 교대 브리핑</span><span class="t2">형곡지구대</span></div>
      </div>
      <div class="topbar-right">{now_str2} 기준 자동생성 · RE:PEAT 112</div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div style="padding:24px 32px;max-width:1380px;margin:0 auto">',unsafe_allow_html=True)
    st.markdown(MV.render_briefing_map_svg(top3,height=160),unsafe_allow_html=True)
    st.markdown("**오늘 우선 확인 지점 TOP3**")
    cols=st.columns(3)
    for col,card in zip(cols,top3+[None]*(3-len(top3))):
        with col:
            if not card: st.markdown('<div class="hc hc-n">데이터 부족</div>',unsafe_allow_html=True); continue
            cls="hc-u" if card["사유"]=="인계메모 긴급" else("hc-a" if card["사유"]=="재발가속" else "hc-n")
            tc3={"hc-u":"#DC2626","hc-a":"#D97706","hc-n":"#1B4FBB"}[cls]
            st.markdown(f"""<div class="hc {cls}">
              <span class="brief-tag" style="background:{tc3}">{card["사유"]}</span>
              <p style="font-family:ui-monospace,monospace;font-size:1.1rem;font-weight:700;margin:6px 0 3px">{card["장소코드"]}</p>
              <p style="font-size:.83rem;margin:0 0 7px">{card["요약"]}</p>
              <p style="font-size:.8rem;font-weight:700;margin:0">▶ {card["추천행동"]}</p>
              <p style="font-size:.7rem;color:#6B7280;margin:5px 0 0">{card["출처"]}</p>
            </div>""",unsafe_allow_html=True)
    st.markdown("---")
    n_ac=len(accel); n_ex=len(clean_df)-len(conc_pool); n_fc=int((tracks["트랙"]=="시설대응/협업").sum()); n_pd=int((tracks["트랙"]=="확인대기").sum())
    metric_cards([("Power Few 스냅샷",f"상위1% {conc_adj['top1']['share']*100:.0f}%",f"반복장소 {conc_adj['n_places']:,}곳","#1B4FBB"),("재발가속",f"{n_ac}곳","간격 짧아진 지점",RISK),("시설대응 확인",f"{n_fc}곳","경찰관 확인 거점",CALM),("자동 제외",f"{n_ex:,}건","아티팩트·제도변화","#9CA3AF")])
    st.markdown("**전 근무자 인계사항**")
    for n in reversed(st.session_state.handoff_notes):
        ug=badge("긴급","b-accel") if n.get("긴급") else ""
        st.markdown(f'<div class="note-row">✏️ <div style="flex:1"><b>{n.get("장소코드") or "(미지정)"}</b> · {n["내용"]}<div style="font-size:.72rem;color:#9CA3AF">{n["작성자"]} · {n["작성시각"]}</div></div>{ug}</div>',unsafe_allow_html=True)
    if not st.session_state.handoff_notes: st.caption("등록된 인계사항이 없습니다.")
    with st.form("hf",clear_on_submit=True):
        hc1,hc2,hc3=st.columns([2,1,1])
        hl=hc1.text_input("장소코드(선택)"); hw=hc2.text_input("작성자"); hu=hc3.checkbox("긴급")
        hcont=st.text_area("인계사항")
        if st.form_submit_button("등록") and hcont.strip():
            st.session_state.handoff_notes.append({"장소코드":hl.strip() or None,"내용":hcont.strip(),"작성자":hw.strip() or "미상","작성시각":datetime.now().strftime("%H:%M"),"긴급":hu})
            st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)
