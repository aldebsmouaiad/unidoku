# pages/02_Dashboard.py
from __future__ import annotations

import base64
import html
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.charts import radar_ist_soll
from core.state import init_session_state
from core.exporter import make_csv_bytes

TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"


# ---------------------------------------------------------------------
# Design: 1:1 aus Gesamtübersicht übernommen (Tokens, Plot-Cards, Tabelle, Modal)
# ---------------------------------------------------------------------
def _inject_dashboard_css() -> None:
    """Dashboard exakt wie Gesamtübersicht (Cards/Typo) + Measures-Table-Style + robustes components.html Layout."""
    dark = bool(st.session_state.get("ui_dark_mode", st.session_state.get("dark_mode", False)))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    header_bg = "rgba(255,255,255,0.08)" if dark else "rgba(127,127,127,0.10)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

    card_bg = "rgba(255,255,255,0.05)" if dark else "rgba(255,255,255,1.00)"
    card_solid = "#111827" if dark else "#ffffff"
    text_color = "rgba(255,255,255,0.92)" if dark else "#111111"

    df_bg = "#0f172a" if dark else "#ffffff"
    df_header = "#0b1220" if dark else "#f3f4f6"
    df_grid = "rgba(255,255,255,0.10)" if dark else "rgba(0,0,0,0.10)"
    df_hover = "rgba(202,116,6,0.18)" if dark else "rgba(202,116,6,0.10)"
    df_text = "rgba(250,250,250,0.92)" if dark else "#111111"
    df_muted = "rgba(250,250,250,0.70)" if dark else "rgba(0,0,0,0.60)"

    toolbar_bg = "rgba(17,24,39,0.85)" if dark else "rgba(255,255,255,0.92)"
    toolbar_hover = "rgba(202,116,6,0.25)" if dark else "rgba(202,116,6,0.14)"
    icon_green = "#639A00"

    st.markdown(
        f"""
<style>
  /* =========================
     BASE-LOOK (wie Gesamtübersicht)
     ========================= */
  .rgm-page {{
    max-width: 1200px;
    margin: 0 auto;
    padding-bottom: 6px;
  }}

  .rgm-h1 {{
    font-size: 30px;
    font-weight: 850;
    line-height: 1.15;
    margin: 0 0 6px 0;
    color: var(--rgm-text, #111);
  }}

  .rgm-lead {{
    font-size: 15px;
    line-height: 1.75;
    color: var(--rgm-text, #111);
    opacity: 0.92;
    margin: 0;
  }}

  .rgm-muted {{
    font-size: 15px;
    line-height: 1.75;
    color: var(--rgm-text, #111);
    opacity: 0.92;
  }}

  .rgm-hero {{
    background: var(--rgm-card-solid, #fff);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    padding: 18px 18px 14px 18px;
    box-shadow: var(--rgm-shadow);
  }}

  .rgm-accent-line {{
    height: 3px;
    width: 96px;
    border-radius: 999px;
    margin: 10px 0 14px 0;
    background: linear-gradient(90deg, var(--rgm-td-blue), var(--rgm-og-orange));
  }}

  .rgm-divider {{
    height: 1px;
    width: 100%;
    background: var(--rgm-border);
    margin: 22px 0 16px 0;
  }}

  .rgm-section-title {{
    font-weight: 850;
    font-size: 16px;
    margin: 0 0 14px 0;
    color: var(--rgm-text);
  }}

  /* =========================
     Tokens + Container
     ========================= */
  div[data-testid="stAppViewContainer"] {{
    --rgm-td-blue: {TD_BLUE};
    --rgm-og-orange: {OG_ORANGE};
    --rgm-border: {border};
    --rgm-soft: {soft_bg};
    --rgm-header-bg: {header_bg};
    --rgm-card-bg: {card_bg};
    --rgm-card-solid: {card_solid};
    --rgm-text: {text_color};
    --rgm-df-bg: {df_bg};
    --rgm-df-header: {df_header};
    --rgm-df-grid: {df_grid};
    --rgm-df-hover: {df_hover};
    --rgm-df-text: {df_text};
    --rgm-df-muted: {df_muted};
    --rgm-toolbar-bg: {toolbar_bg};
    --rgm-toolbar-hover: {toolbar_hover};
    --rgm-icon-green: {icon_green};
    --rgm-shadow: {shadow};
  }}

  div[data-testid="stAppViewContainer"] .block-container {{
    max-width: 1200px;
    margin: 0 auto;
    padding-top: 1.0rem;
    padding-bottom: 6.0rem;
  }}

  /* Anchor links aus */
  a.anchor-link,
  a.header-anchor,
  a[data-testid="stHeaderLink"],
  a[aria-label="Anchor link"],
  a[data-testid="stMarkdownAnchorLink"],
  svg[data-testid="stMarkdownAnchorIcon"] {{
    display: none !important;
  }}

  button[kind="primary"] {{
    border-radius: 12px !important;
    font-weight: 850 !important;
  }}

  /* =========================
     Plotly-Card wie Gesamtübersicht
     (für st.plotly_chart – falls irgendwo verwendet)
     ========================= */
  div[data-testid="stPlotlyChart"]{{
    background: var(--rgm-card-solid);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    box-shadow: var(--rgm-shadow);
    padding: 12px 12px 10px 12px;
    margin-top: 12px;
    overflow: hidden;
  }}

  /* Modebar Look wie Gesamtübersicht */
  div[data-testid="stPlotlyChart"] .js-plotly-plot .modebar{{
    top: 10px !important;
    right: 10px !important;
    z-index: 50 !important;
  }}
  div[data-testid="stPlotlyChart"] .modebar{{ background: transparent !important; }}
  div[data-testid="stPlotlyChart"] .modebar-group{{
    background: var(--rgm-toolbar-bg) !important;
    border: 1px solid var(--rgm-border) !important;
    border-radius: 10px !important;
    padding: 2px 4px !important;
    box-shadow: 0 10px 22px rgba(0,0,0,0.25) !important;
    backdrop-filter: blur(8px);
    margin: 0 !important;
  }}
  div[data-testid="stPlotlyChart"] .modebar-btn path{{ fill: var(--rgm-text) !important; }}
  div[data-testid="stPlotlyChart"] .modebar-btn:hover{{
    background: var(--rgm-toolbar-hover) !important;
    border-radius: 8px !important;
  }}

  /* =========================
     Measures/Result-Card + Toolbar + Modal
     ========================= */
  .rgm-measures-card {{
    position: relative;
    --rgm-measures-toolbar-space: 44px;
    padding-top: var(--rgm-measures-toolbar-space);
    background: var(--rgm-card-solid);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    box-shadow: var(--rgm-shadow);
    overflow: hidden;
    margin-top: 12px;
  }}

  .rgm-measures-toolbar {{
    position: absolute;
    top: 2px;
    right: 2px;
    z-index: 30;
    display: flex;
    gap: 8px;
    background: var(--rgm-toolbar-bg);
    border: 1px solid var(--rgm-border);
    border-radius: 10px;
    padding: 4px 6px;
    box-shadow: 0 10px 22px rgba(0,0,0,0.25);
    backdrop-filter: blur(8px);
  }}

  a.rgm-tool-btn {{
    width: 34px;
    height: 30px;
    border-radius: 8px;
    border: 0;
    background: transparent;
    color: var(--rgm-icon-green);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }}
  a.rgm-tool-btn:hover {{ background: var(--rgm-toolbar-hover); }}
  .rgm-icon {{
    width: 18px;
    height: 18px;
    display: block;
  }}

  .rgm-measures-scroll {{
    max-height: calc(420px - var(--rgm-measures-toolbar-space));
    overflow: auto;
    background: var(--rgm-card-solid);
  }}

  table.rgm-measures-table thead th{{
    background-color: var(--rgm-df-header) !important;
    color: var(--rgm-df-text) !important;
    opacity: 1 !important;
    position: sticky;
    top: 0;
    z-index: 50;
    border-bottom: 1px solid var(--rgm-df-grid) !important;
    background-clip: padding-box;
  }}

  table.rgm-measures-table{{
    width: 100%;
    table-layout: fixed;
  }}

  td.rgm-num {{
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }}

  td.rgm-wrap {{
    white-space: normal;
    word-break: break-word;
    overflow-wrap: anywhere;
    line-height: 1.35;
  }}

  td.rgm-nowrap {{ white-space: nowrap; }}
  .rgm-nowrap-cell{{
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: block;
  }}

  /* Clamp (nur inneres DIV) */
  .rgm-cell {{
    display: block;
    white-space: normal;
    word-break: break-word;
    overflow-wrap: anywhere;
    line-height: 1.35;
  }}
  .rgm-clamp-2 {{
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
  }}
  .rgm-clamp-3 {{
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
    overflow: hidden;
  }}
  .rgm-clamp-6 {{
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 6;
    overflow: hidden;
  }}
  .rgm-clamp-8 {{
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 8;
    overflow: hidden;
  }}

  /* Scrollbar */
  .rgm-measures-scroll::-webkit-scrollbar {{ height: 10px; width: 10px; }}
  .rgm-measures-scroll::-webkit-scrollbar-thumb {{
    background: var(--rgm-df-grid);
    border-radius: 999px;
  }}
  .rgm-measures-scroll::-webkit-scrollbar-track {{ background: transparent; }}

  /* ===== Modal robust ===== */
  #rgm-close {{
    position: fixed;
    top: 0;
    left: 0;
    width: 1px;
    height: 1px;
    opacity: 0;
    pointer-events: none;
  }}

  .rgm-modal {{
    display: none;
    position: fixed;
    inset: 0;
    z-index: 2147483647;
  }}
  .rgm-modal:target {{
    display: block;
  }}

  .rgm-modal-backdrop {{
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.55);
    z-index: 0;
    display: block;
    text-decoration: none;
  }}

  .rgm-modal-content {{
    position: absolute;
    inset: 14px;
    background: var(--rgm-card-solid);
    border: 1px solid var(--rgm-border);
    border-radius: 16px;
    box-shadow: 0 16px 42px rgba(0,0,0,0.55);
    overflow: hidden;
    z-index: 1;
  }}

  .rgm-modal-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-bottom: 1px solid var(--rgm-border);
    background: rgba(255,255,255,0.04);
  }}

  .rgm-modal-title {{
    font-weight: 900;
    color: var(--rgm-text);
    font-size: 16px;
  }}

  a.rgm-modal-close {{
    width: 40px;
    height: 34px;
    border-radius: 10px;
    border: 1px solid var(--rgm-border);
    background: var(--rgm-toolbar-bg);
    color: var(--rgm-icon-green);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }}
  a.rgm-modal-close:hover {{
    background: var(--rgm-toolbar-hover);
  }}

  .rgm-modal-body {{
    height: calc(100% - 56px);
    overflow: auto;
    background: var(--rgm-card-solid);
  }}

  .rgm-modal-body table.rgm-measures-table thead th {{
    position: sticky;
    top: 0;
    z-index: 20;
    background-color: var(--rgm-df-header) !important;
    border-bottom: 1px solid var(--rgm-df-grid) !important;
    box-shadow: 0 1px 0 var(--rgm-df-grid);
  }}

  .rgm-modal-body table.rgm-measures-table {{
    min-width: 980px;
  }}

  @media (max-width: 900px) {{
    div[data-testid="stAppViewContainer"] .block-container {{
      padding-left: 0.7rem;
      padding-right: 0.7rem;
    }}
    .rgm-h1 {{ font-size: 26px; }}
    .rgm-hero {{ padding: 16px; }}
  }}

  /* =========================================================
     components.html / iframe – ROBUST (wie Gesamtübersicht)
     ========================================================= */
  div[data-testid="stAppViewContainer"] div[data-testid="stHtml"],
  div[data-testid="stAppViewContainer"] div[data-testid="stHtml"] > div,
  div[data-testid="stAppViewContainer"] div[data-testid="stCustomComponentV1"],
  div[data-testid="stAppViewContainer"] div[data-testid="stCustomComponentV1"] > div,
  div[data-testid="stAppViewContainer"] div[data-testid="stIFrame"],
  div[data-testid="stAppViewContainer"] div[data-testid="stIFrame"] > div,
  div[data-testid="stAppViewContainer"] div[data-testid="stIframe"],
  div[data-testid="stAppViewContainer"] div[data-testid="stIframe"] > div {{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
  }}

  div[data-testid="stAppViewContainer"] div.element-container:has(iframe[title="streamlit.components.v1.html"]),
  div[data-testid="stAppViewContainer"] div[data-testid="stElementContainer"]:has(iframe[title="streamlit.components.v1.html"]),
  div[data-testid="stAppViewContainer"] div:has(> iframe[title="streamlit.components.v1.html"]) {{
    width: 100% !important;
    max-width: 100% !important;
    display: block !important;
    flex: 1 1 0% !important;
    min-width: 0 !important;
  }}

  div[data-testid="stAppViewContainer"] iframe[title="streamlit.components.v1.html"],
  div[data-testid="stAppViewContainer"] iframe[srcdoc] {{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    display: block !important;
    border: 0 !important;
  }}
</style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def get_answers() -> dict:
    return st.session_state.get("answers", {}) or {}


def after_dash(text: str) -> str:
    """Gibt nur den Teil nach dem ersten '-' zurück (getrimmt)."""
    s = "" if text is None else str(text)
    return s.split("-", 1)[1].strip() if "-" in s else s.strip()


def _scale_legend_centered() -> None:
    st.markdown(
        """
<style>
  .rgm-legend-wrap { display:flex; justify-content:center; margin-top: 10px; }
  .rgm-legend-box {
    padding: 8px 14px;
    border: 1px solid var(--rgm-border);
    border-radius: 10px;
    background: var(--rgm-card-bg);
    color: var(--rgm-text);
    font-size: 14px;
    line-height: 1.4;
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    align-items: center;
  }
  .rgm-legend-box .rgm-num { color: #d62728 !important; font-weight: 700 !important; }
</style>

<div class="rgm-legend-wrap">
  <div class="rgm-legend-box">
    <span style="font-weight:600;">Legende:</span>
    <span><span class="rgm-num">1</span> - Initial</span>
    <span><span class="rgm-num">2</span> - Gemanagt</span>
    <span><span class="rgm-num">3</span> - Definiert</span>
    <span><span class="rgm-num">4</span> - Quantitativ gemanagt</span>
    <span><span class="rgm-num">5</span> - Optimiert</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _escape(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, float) and x != x:
        return ""
    return html.escape(str(x))


def _icons_svg() -> tuple[str, str, str]:
    """(download_svg, fullscreen_svg, close_svg) – stroke=currentColor."""
    download_svg = """
<svg class="rgm-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M12 3v10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  <path d="M8 11l4 4 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M4 21h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg>
""".strip()

    fullscreen_svg = """
<svg class="rgm-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M9 4H4v5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M15 4h5v5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M9 20H4v-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M15 20h5v-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
""".strip()

    close_svg = """
<svg class="rgm-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  <path d="M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg>
""".strip()

    return download_svg, fullscreen_svg, close_svg


# ---------------------------------------------------------------------
# Result table (Dashboard) im exakten Measures-Look inkl. Toolbar + Modal
# ---------------------------------------------------------------------
def _build_dashboard_result_table_html(df_view: pd.DataFrame, compact: bool) -> str:
    cols = list(df_view.columns)

    width_map = {
        "Kürzel": 90,
        "Themenbereich": 300,
        "Ist-Reifegrad": 120,
        "Soll-Reifegrad": 120,
    }

    colgroup = "".join(f'<col style="width:{int(width_map.get(c, 180))}px;">' for c in cols)
    thead = "".join(f"<th>{_escape(c)}</th>" for c in cols)

    nowrap_cols = {"Kürzel"}
    wrap_cols = {"Themenbereich"}
    num_cols = {"Ist-Reifegrad", "Soll-Reifegrad"}

    clamp_map_compact = {"Themenbereich": "rgm-clamp-3"}
    clamp_map_modal = {"Themenbereich": "rgm-clamp-8"}
    clamp_map = clamp_map_compact if compact else clamp_map_modal

    rows_html: list[str] = []
    for _, row in df_view.iterrows():
        tds: list[str] = []
        for c in cols:
            val = "" if pd.isna(row[c]) else str(row[c])
            safe = _escape(val)

            if c in num_cols:
                tds.append(f'<td class="rgm-num" title="{safe}">{safe}</td>')
                continue

            if c in nowrap_cols:
                tds.append(
                    f'<td class="rgm-nowrap" title="{safe}">'
                    f'<div class="rgm-nowrap-cell">{safe}</div></td>'
                )
                continue

            if c in wrap_cols:
                clamp_cls = clamp_map.get(c, "")
                inner_cls = ("rgm-cell " + clamp_cls).strip() if clamp_cls else "rgm-cell"
                tds.append(
                    f'<td class="rgm-wrap" title="{safe}"><div class="{inner_cls}">{safe}</div></td>'
                )
                continue

            tds.append(f'<td title="{safe}">{safe}</td>')

        rows_html.append("<tr>" + "".join(tds) + "</tr>")

    table_class = "rgm-measures-table rgm-measures-compact" if compact else "rgm-measures-table rgm-measures-full"

    return (
        f'<table class="{table_class}">'
        f"<colgroup>{colgroup}</colgroup>"
        f"<thead><tr>{thead}</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        f"</table>"
    )


def _render_dashboard_result_table(df_view: pd.DataFrame, csv_filename: str = "ergebnis_tabelle.csv") -> None:
    csv_bytes = make_csv_bytes(df_view)

    if not str(csv_filename).lower().endswith(".csv"):
        csv_filename = f"{csv_filename}.csv"

    csv_b64 = base64.b64encode(csv_bytes).decode("utf-8")
    csv_href = f"data:text/csv;charset=utf-8;base64,{csv_b64}"

    modal_id = "rgmDashboardResultModal"
    download_svg, fullscreen_svg, close_svg = _icons_svg()

    table_normal = _build_dashboard_result_table_html(df_view, compact=True)
    table_modal = _build_dashboard_result_table_html(df_view, compact=False)

    html_block = (
        f'<div id="rgm-close"></div>'
        f'<div class="rgm-measures-card">'
        f'  <div class="rgm-measures-toolbar">'
        f'    <a class="rgm-tool-btn" href="{csv_href}" download="{_escape(csv_filename)}" '
        f'       title="CSV herunterladen" aria-label="CSV herunterladen">{download_svg}</a>'
        f'    <a class="rgm-tool-btn" href="#{modal_id}" title="Vollbild" aria-label="Vollbild">{fullscreen_svg}</a>'
        f"  </div>"
        f'  <div class="rgm-measures-scroll">{table_normal}</div>'
        f"</div>"
        f'<div id="{modal_id}" class="rgm-modal">'
        f'  <a href="#rgm-close" class="rgm-modal-backdrop" aria-label="Schließen"></a>'
        f'  <div class="rgm-modal-content" role="dialog" aria-modal="true">'
        f'    <div class="rgm-modal-header">'
        f'      <div class="rgm-modal-title">Ergebnis in Tabellenform</div>'
        f'      <a class="rgm-modal-close" href="#rgm-close" title="Schließen" aria-label="Schließen">{close_svg}</a>'
        f"    </div>"
        f'    <div class="rgm-modal-body">{table_modal}</div>'
        f"  </div>"
        f"</div>"
    )
    st.markdown(html_block, unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Dual Radar Cards: Download wie Gesamtübersicht (Composite: Header + Mini-Legende + Skalen-Legende)
# ---------------------------------------------------------------------
def _render_dual_plot_cards(
    fig_left,
    title_left: str,
    filename_left: str,
    fig_right,
    title_right: str,
    filename_right: str,
) -> None:
    """Zwei Plotly-Radar-Cards in EINEM components.html (Download wie Gesamtübersicht: Plot + Legenden)."""
    if fig_left is None and fig_right is None:
        st.info("Keine Daten vorhanden.")
        return

    dark = bool(st.session_state.get("ui_dark_mode", st.session_state.get("dark_mode", False)))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"
    card_bg = "#111827" if dark else "#ffffff"
    font_color = "rgba(255,255,255,0.92)" if dark else "#111111"
    muted = "rgba(255,255,255,0.70)" if dark else "rgba(0,0,0,0.60)"

    toolbar_bg = "rgba(17,24,39,0.85)" if dark else "rgba(255,255,255,0.92)"
    toolbar_hover = "rgba(202,116,6,0.25)" if dark else "rgba(202,116,6,0.14)"
    icon_green = "#639A00"

    download_svg, fullscreen_svg, _ = _icons_svg()

    def _trace_color(fig, i: int, fallback: str) -> str:
        if fig is None:
            return fallback
        try:
            t = fig.data[i]
            if hasattr(t, "line") and getattr(t.line, "color", None):
                return str(t.line.color)
            if hasattr(t, "marker") and getattr(t.marker, "color", None):
                return str(t.marker.color)
        except Exception:
            pass
        return fallback

    l_ist = _trace_color(fig_left, 0, "#1f77b4")
    l_soll = _trace_color(fig_left, 1, "#ff7f0e")
    r_ist = _trace_color(fig_right, 0, "#1f77b4")
    r_soll = _trace_color(fig_right, 1, "#ff7f0e")

    fig_left_json = "null" if fig_left is None else fig_left.to_json()
    fig_right_json = "null" if fig_right is None else fig_right.to_json()

    initial_height = 600

    html_doc = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <script src="https://cdn.plot.ly/plotly-2.30.0.min.js"></script>
  <style>
    html, body {{
      margin: 0; padding: 0; background: transparent;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      color: {font_color};
    }}

    .rgm-grid{{
      display:grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.9rem;
    }}

    .rgm-card {{
      width: 100%;
      min-width: 0;
      box-sizing: border-box;
      background: {card_bg};
      border: 1px solid {border};
      border-radius: 14px;
      box-shadow: {shadow};
      overflow: hidden;
      padding: 12px;
      display: flex;
      flex-direction: column;
      --plotH: 520px;
    }}

    .rgm-card.td {{ border: 2px solid {TD_BLUE}; }}
    .rgm-card.og {{ border: 2px solid {OG_ORANGE}; }}

    .rgm-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
      padding: 2px 2px 8px 2px;
    }}

    .rgm-title {{
      font-weight: 850;
      font-size: 16px;
      line-height: 1.2;
      color: {font_color};
    }}

    .rgm-mini-legend {{
      margin-top: 6px;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      font-size: 12.5px;
      color: {muted};
    }}

    .rgm-item {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
    }}

    .rgm-swatch {{
      width: 18px;
      height: 3px;
      border-radius: 999px;
      display: inline-block;
    }}

    .rgm-swatch-toggle{{
      cursor: pointer;
      position: relative;
    }}
    .rgm-swatch-toggle::before{{
      content: "";
      position: absolute;
      left: -10px;
      right: -10px;
      top: -8px;
      bottom: -8px;
      background: transparent;
    }}
    .rgm-swatch-toggle.off{{
      opacity: 0.25;
    }}

    .rgm-toolbar {{
      display: flex;
      gap: 8px;
      background: {toolbar_bg};
      border: 1px solid {border};
      border-radius: 10px;
      padding: 4px 6px;
      box-shadow: 0 10px 22px rgba(0,0,0,0.25);
      backdrop-filter: blur(8px);
      flex: 0 0 auto;
    }}

    .rgm-capture-hide-toolbar .rgm-toolbar {{ display: none !important; }}

    .rgm-btn {{
      width: 34px;
      height: 30px;
      border-radius: 8px;
      border: 0;
      background: transparent;
      color: {icon_green};
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      padding: 0;
    }}
    .rgm-btn:hover {{ background: {toolbar_hover}; }}
    .rgm-icon {{ width: 18px; height: 18px; display: block; }}

    .rgm-plot {{
      width: 100%;
      height: var(--plotH);
      min-width: 0;
    }}
  </style>
</head>

<body>
  <div class="rgm-grid">
    <div id="cardL" class="rgm-card td">
      <div id="headL" class="rgm-head">
        <div>
          <div class="rgm-title">{html.escape(title_left)}</div>
          <div class="rgm-mini-legend">
            <span class="rgm-item">
              <span class="rgm-swatch rgm-swatch-toggle" data-trace="0" role="button" tabindex="0"
                    aria-label="Ist-Reifegrad ein-/ausblenden" style="background:{l_ist};"></span>
              Ist-Reifegrad
            </span>
            <span class="rgm-item">
              <span class="rgm-swatch rgm-swatch-toggle" data-trace="1" role="button" tabindex="0"
                    aria-label="Soll-Reifegrad ein-/ausblenden" style="background:{l_soll};"></span>
              Soll-Reifegrad
            </span>
          </div>
        </div>
        <div class="rgm-toolbar">
          <button id="dlL" class="rgm-btn" title="Herunterladen" aria-label="Herunterladen">{download_svg}</button>
          <button id="fsL" class="rgm-btn" title="Vollbild" aria-label="Vollbild">{fullscreen_svg}</button>
        </div>
      </div>
      <div id="plotL" class="rgm-plot"></div>
    </div>

    <div id="cardR" class="rgm-card og">
      <div id="headR" class="rgm-head">
        <div>
          <div class="rgm-title">{html.escape(title_right)}</div>
          <div class="rgm-mini-legend">
            <span class="rgm-item">
              <span class="rgm-swatch rgm-swatch-toggle" data-trace="0" role="button" tabindex="0"
                    aria-label="Ist-Reifegrad ein-/ausblenden" style="background:{r_ist};"></span>
              Ist-Reifegrad
            </span>
            <span class="rgm-item">
              <span class="rgm-swatch rgm-swatch-toggle" data-trace="1" role="button" tabindex="0"
                    aria-label="Soll-Reifegrad ein-/ausblenden" style="background:{r_soll};"></span>
              Soll-Reifegrad
            </span>
          </div>
        </div>
        <div class="rgm-toolbar">
          <button id="dlR" class="rgm-btn" title="Herunterladen" aria-label="Herunterladen">{download_svg}</button>
          <button id="fsR" class="rgm-btn" title="Vollbild" aria-label="Vollbild">{fullscreen_svg}</button>
        </div>
      </div>
      <div id="plotR" class="rgm-plot"></div>
    </div>
  </div>

  <script>
    const FIG_L = {fig_left_json};
    const FIG_R = {fig_right_json};

    const config = {{
      displayModeBar: false,
      responsive: true,
      scrollZoom: false,
      doubleClick: false,
      editable: false
    }};

    const EXPORT_BG = {card_bg!r};
    const EXPORT_TEXT = {font_color!r};
    const EXPORT_BORDER = {border!r};
    const EXPORT_RED = "#d62728";

    function downloadDataUrl(dataUrl, filename) {{
      const a = document.createElement("a");
      a.href = dataUrl;
      a.download = filename.endsWith(".png") ? filename : (filename + ".png");
      document.body.appendChild(a);
      a.click();
      a.remove();
    }}

    function roundRect(ctx, x, y, w, h, r) {{
      const rr = Math.min(r, w / 2, h / 2);
      ctx.beginPath();
      ctx.moveTo(x + rr, y);
      ctx.arcTo(x + w, y, x + w, y + h, rr);
      ctx.arcTo(x + w, y + h, x, y + h, rr);
      ctx.arcTo(x, y + h, x, y, rr);
      ctx.arcTo(x, y, x + w, y, rr);
      ctx.closePath();
    }}

    function getScaleLegendMetrics(ctx, imgW, scale) {{
      const pad = 14 * scale;
      const topGap = 12 * scale;
      const lineStep = 22 * scale;

      const items = [
        ["1", "Initial"],
        ["2", "Gemanagt"],
        ["3", "Definiert"],
        ["4", "Quantitativ gemanagt"],
        ["5", "Optimiert"],
      ];

      const fontLabel = "700 " + (18 * scale) + "px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif";
      const fontNum   = "800 " + (18 * scale) + "px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif";
      const fontTail  = "600 " + (17 * scale) + "px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif";

      ctx.font = fontLabel;
      const label = "Legende:";
      const labelW = ctx.measureText(label).width;

      let contentW = labelW + 14 * scale;

      for (const [num, txt] of items) {{
        ctx.font = fontNum;
        const nW = ctx.measureText(num).width;

        ctx.font = fontTail;
        const tail = ` - ${{txt}}`;
        const tailW = ctx.measureText(tail).width;

        const itemW = nW + (2 * scale) + tailW + (18 * scale);
        contentW += itemW;
      }}

      const minW = 520 * scale;
      const maxW = imgW - 90 * scale;
      const boxW = Math.max(minW, Math.min(maxW, contentW + 2 * pad));

      const avail = boxW - 2 * pad;

      let lines = 1;
      let cx = labelW + 14 * scale;

      for (const [num, txt] of items) {{
        ctx.font = fontNum;
        const nW = ctx.measureText(num).width;

        ctx.font = fontTail;
        const tail = ` - ${{txt}}`;
        const tailW = ctx.measureText(tail).width;

        const itemW = nW + (2 * scale) + tailW + (18 * scale);

        if (cx + itemW > avail) {{
          lines += 1;
          cx = itemW;
        }} else {{
          cx += itemW;
        }}
      }}

      const lastBaseline = pad + (22 * scale) + (lines - 1) * lineStep;
      const bottomExtra = 12 * scale;
      const boxH = Math.max(64 * scale, lastBaseline + bottomExtra + pad);

      const totalH = boxH + 2 * topGap;

      return {{ pad, topGap, lineStep, boxW, boxH, totalH, fonts: {{ fontLabel, fontNum, fontTail }} }};
    }}

    function drawScaleLegend(ctx, imgW, yTop, scale, metrics = null) {{
      const m = metrics || getScaleLegendMetrics(ctx, imgW, scale);

      const pad = m.pad;
      const boxH = m.boxH;
      const boxW = m.boxW;

      const x = Math.floor((imgW - boxW) / 2);
      const y = yTop + m.topGap;

      ctx.save();
      ctx.fillStyle = EXPORT_BG;
      ctx.strokeStyle = EXPORT_BORDER;
      ctx.lineWidth = 1 * scale;
      roundRect(ctx, x, y, boxW, boxH, 10 * scale);
      ctx.fill();
      ctx.stroke();

      const items = [
        ["1", "Initial"],
        ["2", "Gemanagt"],
        ["3", "Definiert"],
        ["4", "Quantitativ gemanagt"],
        ["5", "Optimiert"],
      ];

      let cx = x + pad;
      let cy = y + pad + 22 * scale;

      ctx.font = m.fonts.fontLabel;
      ctx.fillStyle = EXPORT_TEXT;
      const label = "Legende:";
      ctx.fillText(label, cx, cy);
      cx += ctx.measureText(label).width + 14 * scale;

      const maxX = x + boxW - pad;

      for (const [num, txt] of items) {{
        ctx.font = m.fonts.fontNum;
        ctx.fillStyle = EXPORT_RED;
        const nW = ctx.measureText(num).width;

        ctx.font = m.fonts.fontTail;
        ctx.fillStyle = EXPORT_TEXT;
        const tail = ` - ${{txt}}`;
        const tailW = ctx.measureText(tail).width;

        const itemW = nW + (2 * scale) + tailW + (18 * scale);

        if (cx + itemW > maxX) {{
          cx = x + pad;
          cy += m.lineStep;
        }}

        ctx.font = m.fonts.fontNum;
        ctx.fillStyle = EXPORT_RED;
        ctx.fillText(num, cx, cy);

        ctx.font = m.fonts.fontTail;
        ctx.fillStyle = EXPORT_TEXT;
        ctx.fillText(tail, cx + nW + 2 * scale, cy);

        cx += itemW;
      }}

      ctx.restore();
      return m.totalH;
    }}

    function loadImage(dataUrl) {{
      return new Promise((resolve, reject) => {{
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = dataUrl;
      }});
    }}

    function drawHeader(ctx, cardW, yTop, scale, title, istColor, sollColor) {{
      const pad = 18 * scale;
      const x = pad;
      const y = yTop + pad + 30 * scale;

      ctx.save();
      ctx.fillStyle = EXPORT_TEXT;
      ctx.font = (900) + " " + (22 * scale) + "px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif";
      ctx.fillText(title || "", x, y);

      const yLeg = y + 26 * scale;
      const lineW = 46 * scale;
      const lineH = 5 * scale;

      ctx.font = (650) + " " + (18 * scale) + "px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif";
      ctx.fillStyle = EXPORT_TEXT;

      let cx = x;

      const items = [
        {{ label: "Ist-Reifegrad", color: istColor }},
        {{ label: "Soll-Reifegrad", color: sollColor }},
      ];

      for (const it of items) {{
        ctx.fillStyle = it.color;
        ctx.fillRect(cx, yLeg - lineH + 2 * scale, lineW, lineH);

        cx += lineW + 14 * scale;

        ctx.fillStyle = EXPORT_TEXT;
        ctx.fillText(it.label, cx, yLeg);

        cx += ctx.measureText(it.label).width + 32 * scale;
      }}

      ctx.restore();

      return 120 * scale;
    }}

    async function exportCardCompositePNG(cardEl, filename, hideToolbar=true, scale=2) {{
      const PLOT_H = 1200;
      const PLOT_W = Math.round(PLOT_H * 1.5);
      const PLOT_SCALE = Math.max(2, Math.min(3, Number(scale) || 3));

      if (!cardEl) return;

      const plotRoot = cardEl.querySelector(".js-plotly-plot");
      if (!plotRoot || typeof Plotly === "undefined") {{
        return;
      }}

      const title = (cardEl.querySelector(".rgm-title")?.textContent || "").trim();
      const sw = cardEl.querySelectorAll(".rgm-swatch-toggle");
      const istCol = sw[0] ? getComputedStyle(sw[0]).backgroundColor : "#1f77b4";
      const sollCol = sw[1] ? getComputedStyle(sw[1]).backgroundColor : "#ff7f0e";

      if (hideToolbar) cardEl.classList.add("rgm-capture-hide-toolbar");

      try {{
        const dataUrl = await Plotly.toImage(plotRoot, {{
          format: "png",
          width: PLOT_W,
          height: PLOT_H,
          scale: PLOT_SCALE
        }});

        const img = await loadImage(dataUrl);

        const S = PLOT_SCALE;
        const PAD = 18 * S;
        const R = 16 * S;

        const HEADER_H = 110 * S;

        const tmp = document.createElement("canvas");
        const tctx = tmp.getContext("2d");

        const legendMetrics = getScaleLegendMetrics(tctx, img.width, S);
        const LEGEND_H = legendMetrics.totalH;

        const cardH = HEADER_H + img.height + LEGEND_H;
        const cardW = img.width;

        const out = document.createElement("canvas");
        out.width = cardW + 2 * PAD;
        out.height = cardH + 2 * PAD;

        const ctx = out.getContext("2d");

        ctx.fillStyle = EXPORT_BG;
        ctx.fillRect(0, 0, out.width, out.height);

        ctx.save();
        ctx.translate(PAD, PAD);
        ctx.fillStyle = EXPORT_BG;
        ctx.strokeStyle = EXPORT_BORDER;
        ctx.lineWidth = 2 * S;
        roundRect(ctx, 0, 0, cardW, cardH, R);
        ctx.fill();
        ctx.stroke();

        drawHeader(ctx, cardW, 0, S, title, istCol, sollCol);

        ctx.drawImage(img, 0, HEADER_H);

        drawScaleLegend(ctx, cardW, HEADER_H + img.height, S, legendMetrics);

        ctx.restore();

        downloadDataUrl(out.toDataURL("image/png"), filename);

      }} finally {{
        if (hideToolbar) cardEl.classList.remove("rgm-capture-hide-toolbar");
      }}
    }}

    function setFrameHeight() {{
      const grid = document.querySelector(".rgm-grid");
      if (!grid) return;
      const h = Math.ceil(grid.getBoundingClientRect().height);
      window.parent.postMessage({{
        isStreamlitMessage: true,
        type: "streamlit:setFrameHeight",
        height: h + 8
      }}, "*");
    }}

    function normalizeLayout(layout) {{
      const L = Object.assign({{}}, layout || {{}});
      L.autosize = true;
      delete L.width;
      delete L.height;
      return L;
    }}

    function safeResize(div) {{
      try {{ Plotly.Plots.resize(div); }} catch(e) {{}}
    }}

    function clamp(v, lo, hi) {{
      return Math.max(lo, Math.min(hi, v));
    }}

    function sleep(ms) {{ return new Promise(r => setTimeout(r, ms)); }}

    function initOne(prefix, FIG, filename) {{
      let plotReady = false;
      const vis = [true, true];

      const card = document.getElementById(prefix === "L" ? "cardL" : "cardR");
      const head = document.getElementById(prefix === "L" ? "headL" : "headR");
      const plotDiv = document.getElementById(prefix === "L" ? "plotL" : "plotR");
      const btnDL = document.getElementById(prefix === "L" ? "dlL" : "dlR");
      const btnFS = document.getElementById(prefix === "L" ? "fsL" : "fsR");

      if (!card || !head || !plotDiv || !btnDL || !btnFS) return;

      if (!FIG) {{
        plotDiv.innerHTML = "<div style='color:{muted}; padding: 12px;'>Keine Daten</div>";
        setTimeout(setFrameHeight, 60);
        return;
      }}

      const LAYOUT = normalizeLayout(FIG.layout);

      const BASE_MARGIN = Object.assign({{ l: 18, r: 18, t: 10, b: 18 }}, (LAYOUT.margin || {{}}));
      const BASE_DOMAIN = (LAYOUT.polar && LAYOUT.polar.domain)
        ? JSON.parse(JSON.stringify(LAYOUT.polar.domain))
        : {{ x: [0, 1], y: [0, 1] }};

      const BASE_ANG_TICK = (((LAYOUT.polar || {{}}).angularaxis || {{}}).tickfont || {{}}).size || 10;
      const BASE_RAD_TICK = (((LAYOUT.polar || {{}}).radialaxis || {{}}).tickfont || {{}}).size || 10;

      let lastFs = false;

      function applyFsLayout(isFs) {{
        if (isFs) {{
          Plotly.relayout(plotDiv, {{
            "margin.l": Math.max(60, BASE_MARGIN.l),
            "margin.r": Math.max(60, BASE_MARGIN.r),
            "margin.t": Math.max(40, BASE_MARGIN.t),
            "margin.b": Math.max(60, BASE_MARGIN.b),
            "polar.domain.x": [0.08, 0.92],
            "polar.domain.y": [0.08, 0.92],
          }});
        }} else {{
          Plotly.relayout(plotDiv, {{
            "margin.l": BASE_MARGIN.l,
            "margin.r": BASE_MARGIN.r,
            "margin.t": BASE_MARGIN.t,
            "margin.b": BASE_MARGIN.b,
            "polar.domain.x": BASE_DOMAIN.x,
            "polar.domain.y": BASE_DOMAIN.y,
          }});
        }}
      }}

      function syncSizes() {{
        const headH = head.getBoundingClientRect().height || 0;
        const w = card.getBoundingClientRect().width || 0;

        const isFs = (document.fullscreenElement === card);
        if (isFs !== lastFs) {{
          applyFsLayout(isFs);
          lastFs = isFs;
        }}

        const minH = (w < 520) ? 340 : 420;
        let plotH = clamp(Math.floor(w - 24), minH, 760);

        if (isFs) {{
          plotH = Math.max(520, Math.floor(window.innerHeight - headH - 32));
        }}

        card.style.setProperty("--plotH", plotH + "px");
        safeResize(plotDiv);
        requestAnimationFrame(() => setFrameHeight());
      }}

      Plotly.newPlot(plotDiv, FIG.data, LAYOUT, config).then(() => {{
        plotReady = true;
        syncSizes();
        setTimeout(setFrameHeight, 120);
      }});

      function toggleTrace(i, swatchEl) {{
        if (!plotReady) return;
        vis[i] = !vis[i];
        Plotly.restyle(plotDiv, {{ visible: vis[i] ? true : "legendonly" }}, [i]);
        swatchEl.classList.toggle("off", !vis[i]);
        swatchEl.setAttribute("aria-pressed", vis[i] ? "true" : "false");
        setTimeout(setFrameHeight, 60);
      }}

      card.querySelectorAll(".rgm-swatch-toggle").forEach((swatch) => {{
        const i = Number(swatch.dataset.trace || "0");

        swatch.addEventListener("click", (e) => {{
          e.stopPropagation();
          toggleTrace(i, swatch);
        }});

        swatch.addEventListener("keydown", (e) => {{
          if (e.key === "Enter" || e.key === " ") {{
            e.preventDefault();
            toggleTrace(i, swatch);
          }}
        }});
      }});

      function applyExportBoost(on) {{
        if (!plotReady) return;

        if (on) {{
          Plotly.relayout(plotDiv, {{
            "margin.l": Math.max(BASE_MARGIN.l, 90),
            "margin.r": Math.max(BASE_MARGIN.r, 90),
            "margin.t": Math.max(BASE_MARGIN.t, 50),
            "margin.b": Math.max(BASE_MARGIN.b, 90),
            "polar.domain.x": [0.04, 0.96],
            "polar.domain.y": [0.04, 0.96],
            "polar.angularaxis.tickfont.size": Math.max(BASE_ANG_TICK, 20),
            "polar.radialaxis.tickfont.size": Math.max(BASE_RAD_TICK, 20),
          }});
        }} else {{
          Plotly.relayout(plotDiv, {{
            "margin.l": BASE_MARGIN.l,
            "margin.r": BASE_MARGIN.r,
            "margin.t": BASE_MARGIN.t,
            "margin.b": BASE_MARGIN.b,
            "polar.domain.x": BASE_DOMAIN.x,
            "polar.domain.y": BASE_DOMAIN.y,
            "polar.angularaxis.tickfont.size": BASE_ANG_TICK,
            "polar.radialaxis.tickfont.size": BASE_RAD_TICK,
          }});
        }}
      }}

      btnDL.addEventListener("click", async () => {{
        if (!plotReady) return;

        try {{
          applyExportBoost(true);
          await sleep(120);
          safeResize(plotDiv);
          await sleep(120);

          await exportCardCompositePNG(card, filename, true, 3);

        }} finally {{
          try {{ applyExportBoost(false); }} catch(e) {{}}
          await sleep(60);
          safeResize(plotDiv);
        }}
      }});

      function toggleFullscreen() {{
        if (document.fullscreenElement) {{
          document.exitFullscreen?.();
        }} else {{
          card.requestFullscreen?.();
        }}
      }}

      btnFS.addEventListener("click", toggleFullscreen);

      const ro = new ResizeObserver(() => syncSizes());
      ro.observe(card);

      const rootRO = new ResizeObserver(() => {{
        requestAnimationFrame(() => syncSizes());
      }});
      rootRO.observe(document.documentElement);

      window.addEventListener("resize", () => setTimeout(syncSizes, 80));
      document.addEventListener("fullscreenchange", () => setTimeout(syncSizes, 120));
    }}

    initOne("L", FIG_L, "{filename_left}");
    initOne("R", FIG_R, "{filename_right}");
  </script>
</body>
</html>
"""
    components.html(html_doc, height=initial_height, scrolling=False)


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main() -> None:
    init_session_state()
    _inject_dashboard_css()

    st.markdown('<div class="rgm-page">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="rgm-hero">
          <div class="rgm-h1">Dashboard</div>
          <div class="rgm-accent-line"></div>
          <p class="rgm-lead">Visualisiertes Ergebnis der Reifegraderhebung.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    model = load_model_config()

    answers = get_answers()
    global_target = float(st.session_state.get("global_target_level", 3.0))
    dim_targets = st.session_state.get("dimension_targets", {}) or {}
    priorities = st.session_state.get("priorities", {}) or {}

    df = build_overview_table(
        model=model,
        answers=answers,
        global_target_level=global_target,
        per_dimension_targets=dim_targets,
        priorities=priorities,
    )

    dark = bool(st.session_state.get("ui_dark_mode", st.session_state.get("dark_mode", False)))

    def tune_plotly(fig):
        """Exakt wie Gesamtübersicht (Radar größer wirkend + einheitliche Farben)."""
        if fig is None:
            return None

        bg = "#111827" if dark else "#ffffff"
        font_color = "rgba(255,255,255,0.92)" if dark else "#111111"
        grid = "rgba(255,255,255,0.14)" if dark else "rgba(0,0,0,0.10)"
        axis_line = "rgba(255,255,255,0.22)" if dark else "rgba(0,0,0,0.14)"

        fig.update_layout(
            template="plotly_dark" if dark else "plotly_white",
            paper_bgcolor=bg,
            plot_bgcolor=bg,
            font=dict(color=font_color),
            margin=dict(l=18, r=18, t=10, b=18),
            title=None,
            showlegend=False,
        )
        fig.update_polars(
            domain=dict(x=[0.06, 0.94], y=[0.06, 0.94]),
            bgcolor=bg,
            radialaxis=dict(
                gridcolor=grid,
                linecolor=axis_line,
                tickfont=dict(color="#d62728", size=12),
                tickcolor="#d62728",
            ),
            angularaxis=dict(
                gridcolor=grid,
                linecolor=axis_line,
                tickfont=dict(color=font_color, size=12),
            ),
        )
        return fig

    # ---------- Radar-Diagramme (exakt wie Gesamtübersicht) ----------
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rgm-section-title">Visualisiertes Ergebnis der Reifegraderhebung</div>', unsafe_allow_html=True)

    if df is None or df.empty:
        st.info("Noch keine Ergebnisse vorhanden – bitte zuerst die Erhebung durchführen.")
    else:
        fig_td = tune_plotly(radar_ist_soll(df, "TD", "TD-Dimensionen", dark=dark))
        fig_og = tune_plotly(radar_ist_soll(df, "OG", "OG-Dimensionen", dark=dark))

        _render_dual_plot_cards(
            fig_left=fig_td,
            title_left="TD-Dimensionen",
            filename_left="reifegrad_radar_td",
            fig_right=fig_og,
            title_right="OG-Dimensionen",
            filename_right="reifegrad_radar_og",
        )
        _scale_legend_centered()

    # ---------- Ergebnis in Tabellenform (exakt Measures-Style) ----------
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rgm-section-title">Ergebnis in Tabellenform</div>', unsafe_allow_html=True)

    if df is None or df.empty:
        st.info("Noch keine Ergebnisse vorhanden.")
        can_proceed = False
    else:
        df_view = df[["code", "name", "ist_level", "target_level"]].copy()
        df_view["name"] = df_view["name"].apply(after_dash)
        df_view = df_view.rename(
            columns={
                "code": "Kürzel",
                "name": "Themenbereich",
                "ist_level": "Ist-Reifegrad",
                "target_level": "Soll-Reifegrad",
            }
        )

        for c in ["Ist-Reifegrad", "Soll-Reifegrad"]:
            df_view[c] = pd.to_numeric(df_view[c], errors="coerce").apply(
                lambda x: "" if x != x else f"{float(x):.2f}".rstrip("0").rstrip(".")
            )

        _render_dashboard_result_table(df_view, csv_filename="ergebnis_tabelle.csv")
        can_proceed = True

    # Navigation
    st.markdown("---")
    if st.button(
        "Weiter zur Priorisierung",
        type="primary",
        use_container_width=True,
        disabled=not can_proceed,
    ):
        st.session_state["nav_return_page"] = "Dashboard"
        st.session_state["nav_return_payload"] = {}
        st.session_state["nav_request"] = "Priorisierung"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
