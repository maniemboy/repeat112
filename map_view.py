# -*- coding: utf-8 -*-
"""
리핏112 (RE:PEAT 112) — Power Few Map 모듈 (독립)
================================================================
⚠ v3 데이터에는 실제 주소·좌표가 없다(비식별화 과정에서 제거됨). 이 모듈은
어떤 경우에도 실제 위치를 복원하거나 임의로 좌표를 만들어내지 않는다.
'외부 개발모드'에서는 행정동(COL_DONG)과 장소코드(LOC_BASE_ID)만으로 개략도
(schematic map)를 그린다 — 실제 지리적 위치가 아니라는 걸 화면에 항상 명시한다.

데이터 어댑터 구조 (LocationAdapter)
  SchematicAdapter  (기본값, 외부 개발모드) — 행정동별 구역 + 구역 내 결정론적
                    격자 배치. 좌표를 추정·생성하지 않는다.
  RealCoordAdapter  (내부망 운영모드 전용) — 실제 XY좌표 테이블이 주어졌을 때만
                    동작한다. 좌표가 없으면 예외를 던지고 SchematicAdapter로
                    돌아가라고 안내한다. 이 어댑터는 절대 좌표를 추정하지 않는다.

오프라인 원칙
  외부 지도 API(Google/Kakao/OSM 타일 서버 등)를 호출하지 않는다. 전부 이
  프로세스 안에서 SVG로 직접 그린다. 나중에 로컬 GeoJSON 행정동 경계나 오프라인
  타일 이미지를 쓰고 싶으면 render_* 함수만 교체하면 된다(아래 확장 지점 참고).
"""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod

import pandas as pd

COL_BASE = "LOC_BASE_ID"
COL_DONG = "행정동"

TRACK_STYLE = {
    "맞춤형 순찰": {"color": "#2F6FB0", "shape": "circle", "label": "맞춤형 순찰"},
    "재발가속": {"color": "#D98324", "shape": "circle", "label": "재발가속"},
    "시설대응/협업": {"color": "#8A8578", "shape": "square", "label": "시설거점"},
    "업무량 통계": {"color": "#B9B4A8", "shape": "square", "label": "행정접수 거점"},
    "확인대기": {"color": "#C9CDD3", "shape": "circle", "label": "확인대기"},
}

FILTER_OPTIONS = ["전체", "Power Few", "맞춤형 순찰", "재발가속", "시설·행정"]


def apply_filter(points: pd.DataFrame, filter_key: str) -> pd.DataFrame:
    """지도 상단 필터를 트랙 기준으로 적용한다."""
    if filter_key == "전체":
        return points
    if filter_key == "Power Few":  # 시설·행정 확정분 제외한 전체 반복수요
        return points[points["트랙"].isin(["맞춤형 순찰", "재발가속", "확인대기"])]
    if filter_key == "맞춤형 순찰":
        return points[points["트랙"] == "맞춤형 순찰"]
    if filter_key == "재발가속":
        return points[points["판정사유"].astype(str).str.contains("재발가속", na=False)]
    if filter_key == "시설·행정":
        return points[points["트랙"].isin(["시설대응/협업", "업무량 통계"])]
    return points


def attach_dong(tracks_df: pd.DataFrame, clean_df: pd.DataFrame) -> pd.DataFrame:
    """지점(BASE)별 대표 행정동을 붙인다(가장 빈도 높은 행정동)."""
    if COL_DONG not in clean_df.columns:
        out = tracks_df.copy()
        out[COL_DONG] = "행정동미상"
        return out
    dong_map = clean_df.groupby(COL_BASE)[COL_DONG].agg(
        lambda s: s.value_counts().index[0] if s.notna().any() else "행정동미상"
    )
    out = tracks_df.copy()
    out[COL_DONG] = out[COL_BASE].map(dong_map).fillna("행정동미상")
    return out


# ═══════════════════════════════════════════════════════
# 위치 어댑터
# ═══════════════════════════════════════════════════════
class LocationAdapter(ABC):
    is_real_geo: bool = False

    @abstractmethod
    def layout(self, dong_groups: dict[str, list[str]]):
        """dong_groups: {행정동: [BASE_ID,...]}
        반환: (positions: {BASE_ID:(x,y)} 0~100 캔버스좌표, zones: {행정동: rect dict})
        """
        raise NotImplementedError


class SchematicAdapter(LocationAdapter):
    """
    기본 어댑터(외부 개발모드). 실제 좌표를 전혀 쓰지 않는다.
    행정동을 그리드 구역으로 나누고, 그 구역 안에서 장소코드 정렬 순서에 따라
    결정론적으로 격자 배치한다 — 매 실행마다 같은 자리에 그려지되, 실제
    지리적 의미는 없다(개략도).
    """
    is_real_geo = False

    def layout(self, dong_groups: dict[str, list[str]]):
        dongs = sorted(dong_groups.keys())
        n_dong = max(1, len(dongs))
        cols = max(1, math.ceil(math.sqrt(n_dong)))
        rows = max(1, math.ceil(n_dong / cols))
        zone_w, zone_h = 100 / cols, 100 / rows
        pad = 0.14

        positions: dict[str, tuple[float, float]] = {}
        zones: dict[str, dict] = {}
        for idx, dong in enumerate(dongs):
            zr, zc = divmod(idx, cols)
            x0, y0 = zc * zone_w, zr * zone_h
            zones[dong] = {"x": x0, "y": y0, "w": zone_w, "h": zone_h}
            inner_w, inner_h = zone_w * (1 - 2 * pad), zone_h * (1 - 2 * pad)
            ox, oy = x0 + zone_w * pad, y0 + zone_h * pad

            bases = sorted(dong_groups[dong])
            n = max(1, len(bases))
            pcols = max(1, math.ceil(math.sqrt(n)))
            prows = max(1, math.ceil(n / pcols))
            zones[dong]["cell"] = min(inner_w / pcols, inner_h / prows)
            for i, base in enumerate(bases):
                r, c = divmod(i, pcols)
                px = ox + (c + 0.5) / pcols * inner_w
                py = oy + (r + 0.5) / prows * inner_h
                positions[base] = (px, py)
        return positions, zones


class RealCoordAdapter(LocationAdapter):
    """
    내부망 운영모드 전용 확장 지점. 실제 XY좌표 테이블(coord_table)이 주어졌을
    때만 동작한다. 좌표를 추정·생성하지 않으며, 테이블이 없는 지점은 그리지
    않는다(임의 배치 절대 금지). 좌표 테이블이 아예 없으면 예외를 던진다 —
    호출부(app.py)는 이 경우 SchematicAdapter로 자동 폴백해야 한다.
    """
    is_real_geo = True

    def __init__(self, coord_table: dict[str, tuple[float, float]] | None = None):
        self.coord_table = coord_table or {}

    def layout(self, dong_groups: dict[str, list[str]]):
        if not self.coord_table:
            raise RuntimeError(
                "RealCoordAdapter는 실제 좌표 테이블이 필요합니다 — 내부망 운영모드에서 "
                "좌표 데이터를 연결한 뒤 사용하세요. 좌표가 없으면 SchematicAdapter를 "
                "쓰는 것이 맞습니다(임의 좌표 생성 금지)."
            )
        all_bases = {b for bases in dong_groups.values() for b in bases}
        positions = {b: xy for b, xy in self.coord_table.items() if b in all_bases}
        return positions, {}  # 실좌표 모드는 실제 배경지도 위에 얹는 걸 전제로, 구역 사각형 생략


def make_adapter(mode: str = "schematic", coord_table: dict | None = None) -> LocationAdapter:
    if mode == "real":
        return RealCoordAdapter(coord_table)
    return SchematicAdapter()


# ═══════════════════════════════════════════════════════
# 상세 정보 조회
# ═══════════════════════════════════════════════════════
def location_detail(base_id: str, clean_df: pd.DataFrame, tracks_df: pd.DataFrame,
                    patrol_df: pd.DataFrame) -> dict:
    """지도에서 지점을 선택했을 때 보여줄 상세 정보를 모은다."""
    row = tracks_df[tracks_df[COL_BASE] == base_id]
    if len(row) == 0:
        return {}
    r = row.iloc[0]

    sub = clean_df[clean_df[COL_BASE] == base_id]
    dong = r[COL_DONG] if COL_DONG in tracks_df.columns and pd.notna(r.get(COL_DONG)) else None
    if not dong:
        if COL_DONG in sub.columns and len(sub):
            vc = sub[COL_DONG].value_counts()
            dong = vc.index[0] if len(vc) else "-"
        else:
            dong = "-"

    peak_time = None
    if "시간대구간" in sub.columns and len(sub):
        vc = sub["시간대구간"].value_counts()
        if len(vc):
            peak_time = vc.index[0]

    gap_col = "BASE_직전신고간격_일"
    avg_gap = None
    if gap_col in sub.columns:
        g = sub[gap_col].dropna()
        if len(g):
            avg_gap = round(float(g.mean()), 1)

    action_row = patrol_df[patrol_df[COL_BASE] == base_id]
    action = action_row.iloc[0]["추천행동"] if len(action_row) else None

    return {
        "장소코드": base_id, "행정동": dong,
        "신고건수": int(r["건수"]), "주요유형": r["주요유형"],
        "평균재발간격_일": avg_gap, "주요시간대": peak_time,
        "트랙": r["트랙"], "판정사유": r["판정사유"], "원천": r["원천"],
        "시설유형": r.get("시설유형"), "추천행동": action,
    }


# ═══════════════════════════════════════════════════════
# SVG 렌더링 (일반 대시보드용 — 필터 가능한 전체 지도)
# ═══════════════════════════════════════════════════════
def render_map_svg(points_df: pd.DataFrame, adapter: LocationAdapter | None = None,
                   selected_base: str | None = None, height: int = 480) -> str:
    adapter = adapter or SchematicAdapter()
    if len(points_df) == 0:
        return (f'<div style="height:{height}px;display:flex;align-items:center;'
                f'justify-content:center;color:#8A8578;font-size:.85rem;">'
                f'표시할 지점이 없습니다.</div>')

    dong_groups = points_df.groupby(COL_DONG)[COL_BASE].apply(list).to_dict()
    positions, zones = adapter.layout(dong_groups)

    svg = [f'<svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" '
          f'style="width:100%;height:{height}px;background:#F6F5F1;border-radius:10px;'
          f'border:1px solid #E3E6EC;">']

    if not adapter.is_real_geo:
        for dong, z in zones.items():
            svg.append(
                f'<rect x="{z["x"]:.2f}" y="{z["y"]:.2f}" width="{z["w"]:.2f}" '
                f'height="{z["h"]:.2f}" fill="none" stroke="#E3E6EC" stroke-width="0.25"/>'
            )
            svg.append(
                f'<text x="{z["x"]+0.8:.2f}" y="{z["y"]+2.6:.2f}" font-size="1.9" '
                f'fill="#9AA5B4" font-family="ui-monospace,monospace">{dong}</text>'
            )

    for _, row in points_df.iterrows():
        base = row[COL_BASE]
        if base not in positions:
            continue
        x, y = positions[base]
        style = TRACK_STYLE.get(row["트랙"], {"color": "#9AA5B4", "shape": "circle"})
        color = style["color"]
        is_sel = base == selected_base
        dong = row.get(COL_DONG)
        cell = zones.get(dong, {}).get("cell", 3.0) if not adapter.is_real_geo else 3.0
        base_r = max(0.35, min(1.7, cell * 0.36))
        r = base_r if not is_sel else min(base_r * 1.5, cell * 0.5)
        if is_sel:
            svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r+0.9:.2f}" '
                      f'fill="none" stroke="#12203D" stroke-width="0.35"/>')
        if style["shape"] == "square":
            s = r * 1.7
            svg.append(f'<rect x="{x-s/2:.2f}" y="{y-s/2:.2f}" width="{s:.2f}" '
                      f'height="{s:.2f}" fill="{color}" opacity="0.85"/>')
        else:
            svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" '
                      f'fill="{color}" opacity="0.8"/>')

    svg.append('</svg>')

    legend = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:14px;'
        f'font-size:.76rem;color:#626B7A;"><span style="width:9px;height:9px;'
        f'border-radius:{"2px" if s["shape"]=="square" else "50%"};'
        f'background:{s["color"]};display:inline-block;"></span>{s["label"]}</span>'
        for s in TRACK_STYLE.values()
    )
    note = (
        '<p style="font-size:.72rem;color:#9AA5B4;margin:6px 0 0;">⚠ 실제 지리적 위치가 '
        "아닌 개략도입니다(행정동별 구역 + 지점 격자배치). 실주소·좌표는 사용하지 않습니다."
        if not adapter.is_real_geo else ""
    )
    return "".join(svg) + f'<div style="margin-top:8px;">{legend}</div>{note}'


# ═══════════════════════════════════════════════════════
# SVG 렌더링 (교대 브리핑용 — TOP3 간결 상황지도)
# ═══════════════════════════════════════════════════════
def render_briefing_map_svg(top3_cards: list[dict], height: int = 200) -> str:
    """복잡한 지도 대신 TOP3만 큼직하게 보여주는 간결한 상황지도."""
    if not top3_cards:
        return (f'<div style="height:{height}px;display:flex;align-items:center;'
                f'justify-content:center;color:#8A8578;font-size:.85rem;">'
                f'표시할 우선지점이 없습니다.</div>')

    band_color = {"인계메모 긴급": "#C4433D", "재발가속": "#E8A93B"}
    n = len(top3_cards)
    svg = [f'<svg viewBox="0 0 100 40" preserveAspectRatio="xMidYMid meet" '
          f'style="width:100%;height:{height}px;background:#F6F5F1;border-radius:10px;'
          f'border:1px solid #E3E6EC;">']
    for i, card in enumerate(top3_cards):
        cx = (i + 0.5) / n * 100
        cy = 20
        color = band_color.get(card["사유"], "#16294B")
        svg.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="7" fill="{color}" opacity="0.92"/>')
        svg.append(f'<text x="{cx:.1f}" y="{cy+1.3}" font-size="6" fill="#fff" '
                  f'text-anchor="middle" font-weight="700">{i+1}</text>')
        svg.append(f'<text x="{cx:.1f}" y="{cy+13}" font-size="4.6" fill="#12203D" '
                  f'text-anchor="middle" font-family="ui-monospace,monospace" '
                  f'font-weight="700">{card["장소코드"]}</text>')
        svg.append(f'<text x="{cx:.1f}" y="{cy+18}" font-size="3.6" fill="#626B7A" '
                  f'text-anchor="middle">{card["사유"]}</text>')
    svg.append('</svg>')
    return "".join(svg)
