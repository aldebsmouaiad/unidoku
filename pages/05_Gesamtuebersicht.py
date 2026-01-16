# /workspaces/unidoku/pages/05_Gesamtuebersicht.py
from __future__ import annotations

import base64
import html
from typing import Optional

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core.state import init_session_state
from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.charts import radar_ist_soll
from core.exporter import df_results_for_export, make_csv_bytes, make_pdf_bytes

TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"


def get_answers() -> dict:
    return st.session_state.get("answers", {}) or {}


def _pick_first_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _inject_gesamtuebersicht_css() -> None:
    """Gesamtübersicht-Design (Cards/Typo) + Measures-Tabelle (Sticky Header + Toolbar) + Modal robust."""
    dark = bool(st.session_state.get("dark_mode", False))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    header_bg = "rgba(255,255,255,0.08)" if dark else "rgba(127,127,127,0.10)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

    card_bg = "rgba(255,255,255,0.05)" if dark else "rgba(255,255,255,1.00)"
    card_solid = "#111827" if dark else "#ffffff"
    text_color = "rgba(255,255,255,0.92)" if dark else "#111111"

    df_bg = "#0f172a" if dark else "#ffffff"
    df_header = "#111827" if dark else "#f3f4f6"
    df_grid = "rgba(255,255,255,0.10)" if dark else "rgba(0,0,0,0.10)"
    df_hover = "rgba(202,116,6,0.18)" if dark else "rgba(202,116,6,0.10)"
    df_text = "rgba(250,250,250,0.92)" if dark else "#111111"
    df_muted = "rgba(250,250,250,0.70)" if dark else "rgba(0,0,0,0.60)"

    # Toolbar-Look (wie Tabelle) + grüne Icons
    toolbar_bg = "rgba(17,24,39,0.85)" if dark else "rgba(255,255,255,0.92)"
    toolbar_hover = "rgba(202,116,6,0.25)" if dark else "rgba(202,116,6,0.14)"
    icon_green = "#2f9e44"  # grün wie in deiner Tabellen-Toolbar

    st.markdown(
        f"""
<style>
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

  .rgm-divider {{
    height: 1px;
    width: 100%;
    background: var(--rgm-border);
    margin: 34px 0 22px 0;
  }}

  .rgm-section-title {{
    font-weight: 850;
    font-size: 18px;
    margin: 0 0 14px 0;
    color: var(--rgm-text);
  }}


  /* =========================
   Plotly-Card wie Dashboard
   ========================= */
  div[data-testid="stPlotlyChart"]{{
    background: var(--rgm-card-solid);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    box-shadow: var(--rgm-shadow);
    padding: 12px 12px 10px 12px;
    margin-top: 12px;
    overflow: hidden; /* wie Dashboard (Modebar wird nach innen verschoben) */
  }}

  /* =========================
     Plotly Modebar wie Dashboard (Download + Fullscreen sauber sichtbar)
     ========================= */
  div[data-testid="stPlotlyChart"] .js-plotly-plot .modebar{{
    top: 10px !important;
    right: 10px !important;
    z-index: 50 !important;
  }}

  div[data-testid="stPlotlyChart"] .modebar{{
    background: transparent !important;
  }}

  div[data-testid="stPlotlyChart"] .modebar-group{{
    background: var(--rgm-toolbar-bg) !important;
    border: 1px solid var(--rgm-border) !important;
    border-radius: 10px !important;
    padding: 2px 4px !important;
    box-shadow: 0 10px 22px rgba(0,0,0,0.25) !important;
    backdrop-filter: blur(8px);
    margin: 0 !important;
  }}

  div[data-testid="stPlotlyChart"] .modebar-btn path{{
    fill: var(--rgm-text) !important;
  }}
  div[data-testid="stPlotlyChart"] .modebar-btn:hover{{
    background: var(--rgm-toolbar-hover) !important;
    border-radius: 8px !important;
  }}

  @media (max-width: 900px){{
    div[data-testid="stPlotlyChart"] .js-plotly-plot .modebar{{
      top: 8px !important;
      right: 8px !important;
    }}
  }}


  button[kind="primary"] {{
    border-radius: 12px !important;
    font-weight: 850 !important;
  }}

  /* =========================================================
   FIX: components.html (iframe) MUSS in st.columns volle Breite nehmen
   (sonst entstehen diese schmalen Cards + riesige Lücke in der Mitte)
   ========================================================= */

  /* Der Element-Wrapper, der das iframe enthält */
  div[data-testid="stAppViewContainer"] div.element-container:has(iframe[title="streamlit.components.v1.html"]),
  div[data-testid="stAppViewContainer"] div.element-container:has(> iframe[title="streamlit.components.v1.html"]) {{
    width: 100% !important;
    max-width: 100% !important;
    display: block !important;
    flex: 1 1 0% !important;
    min-width: 0 !important;
  }}

  /* Fallback: irgendein direkter Parent, der das iframe hält */
  div[data-testid="stAppViewContainer"] div:has(> iframe[title="streamlit.components.v1.html"]) {{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
  }}

  /* iframe selbst */
  div[data-testid="stAppViewContainer"] iframe[title="streamlit.components.v1.html"] {{
    width: 100% !important;
    max-width: 100% !important;
    display: block !important;
  }}

  /* Optional: nur für die Row mit den Plot-Frames den Column-Gap klein halten */
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) {{
    gap: 0.35rem  !important;
  }}
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) > div {{
    min-width: 0 !important;
  }}

  /* ===== columns: components.html darf nicht "shrink" werden ===== */
  div[data-testid="column"] div[data-testid="stElementContainer"],
  div[data-testid="column"] div[data-testid="stElementContainer"] > div,
  div[data-testid="column"] div[data-testid="stCustomComponentV1"],
  div[data-testid="column"] div[data-testid="stCustomComponentV1"] > div {{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
  }}

  div[data-testid="column"] iframe[srcdoc],
  div[data-testid="column"] iframe[title="streamlit.components.v1.html"]{{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    display: block !important;
  }}

  
  /* =========================
     Maßnahmen-Card + Toolbar (Modebar-Look)
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
  a.rgm-tool-btn:hover {{
    background: var(--rgm-toolbar-hover);
  }}
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

  table.rgm-measures-table {{
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    background: var(--rgm-df-bg) !important;
    color: var(--rgm-df-text) !important;
    font-size: 14px;
  }}

  /* Sticky Header: bleibt stehen, nur Inhalt scrollt */
  table.rgm-measures-table thead th {{
    position: sticky;
    top: 0;
    z-index: 10;
    background-color: var(--rgm-df-header) !important;
    color: var(--rgm-df-text) !important;
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid var(--rgm-df-grid) !important;
    font-weight: 800;
    white-space: nowrap;
    box-shadow: 0 1px 0 var(--rgm-df-grid);
  }}

  table.rgm-measures-table tbody td {{
    padding: 10px 12px;
    border-bottom: 1px solid var(--rgm-df-grid) !important;
    color: var(--rgm-df-text) !important;
    vertical-align: top;
    background: var(--rgm-df-bg) !important;
  }}

  table.rgm-measures-table tbody tr:hover td {{
    background: var(--rgm-df-hover) !important;
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

  /* Clamp NUR über inneres DIV (niemals auf <td>) */
  .rgm-cell {{
    display: block;
    white-space: normal;
    word-break: break-word;
    overflow-wrap: anywhere;
    line-height: 1.35;
  }}
  .rgm-clamp-1 {{
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 1;
    overflow: hidden;
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

  /* Scrollbar */
  .rgm-measures-scroll::-webkit-scrollbar {{ height: 10px; width: 10px; }}
  .rgm-measures-scroll::-webkit-scrollbar-thumb {{
    background: var(--rgm-df-grid);
    border-radius: 999px;
  }}
  .rgm-measures-scroll::-webkit-scrollbar-track {{ background: transparent; }}

  /* =========================
     Vollbild-Modal (robust, ohne Code-Text)
     ========================= */
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

  /* Modal: Sticky Header + Separator */
  .rgm-modal-body table.rgm-measures-table thead th {{
    position: sticky;
    top: 0;
    z-index: 20;
    background-color: var(--rgm-df-header) !important;
    border-bottom: 1px solid var(--rgm-df-grid) !important;
    box-shadow: 0 1px 0 var(--rgm-df-grid);
  }}

  /* Im Vollbild keine Clamps */
  .rgm-measures-full .rgm-cell {{
    display: block;
  }}

  /* Im Modal horizontal scrollen, falls nötig */
  .rgm-modal-body table.rgm-measures-table {{
    min-width: 1180px;
  }}

  @media (max-width: 900px) {{
    div[data-testid="stAppViewContainer"] .block-container {{
    padding-left: 0.7rem;
    padding-right: 0.7rem;}}
  }}

  /* =========================
   components.html: Wrapper in Streamlit zuverlässig auf volle Breite
   (damit keine 300px-"Mini-Frames" entstehen)
   ========================= */

  /* stHtml Wrapper (components.html landet oft hier) */
  div[data-testid="stAppViewContainer"] div[data-testid="stHtml"],
  div[data-testid="stAppViewContainer"] div[data-testid="stHtml"] > div {{
    width: 100% !important;
    max-width: 100% !important;
  }}

  /* CustomComponent / IFrame Wrapper (variiert je nach Streamlit-Version) */
  div[data-testid="stAppViewContainer"] div[data-testid="stCustomComponentV1"],
  div[data-testid="stAppViewContainer"] div[data-testid="stCustomComponentV1"] > div,
  div[data-testid="stAppViewContainer"] div[data-testid="stIFrame"],
  div[data-testid="stAppViewContainer"] div[data-testid="stIFrame"] > div,
  div[data-testid="stAppViewContainer"] div[data-testid="stIframe"],
  div[data-testid="stAppViewContainer"] div[data-testid="stIframe"] > div {{
    width: 100% !important;
    max-width: 100% !important;
  }}

  /* ElementContainer, der ein components-iframe enthält */
  div[data-testid="stAppViewContainer"] div[data-testid="stElementContainer"]:has(iframe[title="streamlit.components.v1.html"]) {{
    width: 100% !important;
    max-width: 100% !important;
  }}

  /* iframe selbst */
  div[data-testid="stAppViewContainer"] iframe[title="streamlit.components.v1.html"]{{
    width: 100% !important;
    max-width: 100% !important;
    display: block !important;
    border: 0 !important;
  }}

  /* =========================================================
   FINAL FIX (robust):
   Plot-Row mit components.html -> Columns müssen wirklich "stretch" nutzen
   Ergebnis: Cards = volle Column-Breite (wie Button), Gap kontrolliert
   ========================================================= */

  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) {{
    gap: 0.75rem !important;                 /* Abstand zwischen den beiden Cards */
    justify-content: stretch !important;     /* nicht "space-between" */
    align-items: stretch !important;
    width: 100% !important;
  }}

  /* Columns/Children in dieser Row dürfen NICHT schrumpfen und müssen wachsen */
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) > div,
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) > div[data-testid="column"] {{
    flex: 1 1 0% !important;
    min-width: 0 !important;
    width: 0 !important;                    /* sorgt für wirklich gleiche Breite */
  }}

  /* Wrapper der Custom-Component auf 100% zwingen */
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) div[data-testid="stCustomComponentV1"],
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) div[data-testid="stCustomComponentV1"] > div {{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    display: block !important;
  }}

  /* iframe selbst: volle Breite */
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) iframe[title="streamlit.components.v1.html"],
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) iframe[srcdoc] {{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    display: block !important;
    border: 0 !important;
  }}


  /* =========================================================
   FINAL: Plot-Row (components.html) MUSS volle Spaltenbreite nutzen
   -> Cards werden so breit wie der Button/Divider
   ========================================================= */

  /* Die Row, die components.html enthält */
  div[data-testid="stHorizontalBlock"]:has(iframe[srcdoc]),
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) {{
    width: 100% !important;
    align-items: stretch !important;
    gap: 0.9rem !important;              /* elegant, aber nicht zu groß */
  }}

  /* WICHTIG: Columns in dieser Row dürfen nicht shrinken */
  div[data-testid="stHorizontalBlock"]:has(iframe[srcdoc]) > div,
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) > div {{
    flex: 1 1 0% !important;
    min-width: 0 !important;
    max-width: none !important;
  }}

  /* Streamlit-Wrapper der Custom-Components auf 100% */
  div[data-testid="stHorizontalBlock"]:has(iframe[srcdoc]) div[data-testid="stCustomComponentV1"],
  div[data-testid="stHorizontalBlock"]:has(iframe[srcdoc]) div[data-testid="stCustomComponentV1"] > div,
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) div[data-testid="stCustomComponentV1"],
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) div[data-testid="stCustomComponentV1"] > div {{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
  }}

  /* iframe selbst */
  div[data-testid="stHorizontalBlock"]:has(iframe[srcdoc]) iframe,
  div[data-testid="stHorizontalBlock"]:has(iframe[title="streamlit.components.v1.html"]) iframe {{
    width: 100% !important;
    max-width: 100% !important;
    display: block !important;
  }}



</style>
        """,
        unsafe_allow_html=True,
    )


def _clean_overview_df(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    if "ist_level" in d.columns:
        d["ist_level"] = pd.to_numeric(d["ist_level"], errors="coerce")
        d.loc[d["ist_level"].isna() | (d["ist_level"] <= 0), "ist_level"] = pd.NA

    if "target_level" in d.columns:
        d["target_level"] = pd.to_numeric(d["target_level"], errors="coerce")
        d.loc[d["target_level"].isna() | (d["target_level"] <= 0), "target_level"] = pd.NA

    if "ist_level" in d.columns and "target_level" in d.columns:
        d["gap"] = d["target_level"] - d["ist_level"]
        d.loc[d["gap"].notna() & (d["gap"] < 0), "gap"] = 0.0

    d["answered"] = d.get("ist_level").notna() if "ist_level" in d.columns else False
    return d


def _kpi_block(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    d = df.copy()
    n_total = len(d)
    n_answered = int(d["answered"].sum()) if "answered" in d.columns else 0
    d_ans = d[d["answered"]].copy() if n_answered else d.iloc[0:0].copy()

    n_need = int(
        (pd.to_numeric(d_ans.get("gap", 0), errors="coerce").fillna(0.0) > 0).sum()
    ) if n_answered else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Dimensionen", f"{n_total}")
    c2.metric("Bewertet", f"{n_answered} / {n_total}")
    c3.metric("Handlungsbedarf (Gap > 0)", f"{n_need}")

    return n_answered


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


def _escape(x) -> str:
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


def _build_measures_table_html(df_view: pd.DataFrame, compact: bool) -> str:
    cols = list(df_view.columns)

    width_map = {
        "Priorität": 110,
        "Kürzel": 90,
        "Themenbereich": 260,
        "Ist-Reifegrad": 130,
        "Soll-Reifegrad": 140,
        "Gap": 80,
        "Maßnahme": 420,
        "Verantwortlich": 300,
        "Zeitraum": 160,
    }

    colgroup = "".join(
        f'<col style="width:{int(width_map.get(c, 180))}px;">' for c in cols
    )
    thead = "".join(f"<th>{_escape(c)}</th>" for c in cols)

    wrap_cols = {"Themenbereich", "Maßnahme", "Verantwortlich", "Zeitraum"}
    num_cols = {"Ist-Reifegrad", "Soll-Reifegrad", "Gap"}

    clamp_map = {
        "Themenbereich": "rgm-clamp-2",
        "Maßnahme": "rgm-clamp-3",
        "Verantwortlich": "rgm-clamp-2",
        "Zeitraum": "rgm-clamp-1",
    }

    rows_html: list[str] = []
    for _, row in df_view.iterrows():
        tds: list[str] = []
        for c in cols:
            val = "" if pd.isna(row[c]) else str(row[c])
            safe = _escape(val)

            if c in num_cols:
                tds.append(f'<td class="rgm-num" title="{safe}">{safe}</td>')
                continue

            if c in wrap_cols:
                clamp_cls = clamp_map.get(c, "rgm-clamp-2") if compact else ""
                inner_cls = "rgm-cell"
                if compact and clamp_cls:
                    inner_cls += f" {clamp_cls}"
                tds.append(
                    f'<td class="rgm-wrap" title="{safe}"><div class="{inner_cls}">{safe}</div></td>'
                )
                continue

            tds.append(f'<td title="{safe}">{safe}</td>')

        rows_html.append("<tr>" + "".join(tds) + "</tr>")

    table_class = (
        "rgm-measures-table rgm-measures-compact"
        if compact
        else "rgm-measures-table rgm-measures-full"
    )

    return (
        f'<table class="{table_class}">'
        f"<colgroup>{colgroup}</colgroup>"
        f"<thead><tr>{thead}</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        f"</table>"
    )


def _render_measures_block(
    df_view: pd.DataFrame, csv_filename: str = "geplante_massnahmen.csv"
) -> None:
    """Geplante Maßnahmen: Toolbar-Icons (Download + Vollbild)"""
    csv_bytes = make_csv_bytes(df_view)

    if not str(csv_filename).lower().endswith(".csv"):
        csv_filename = f"{csv_filename}.csv"

    # Toolbar-Icon Download
    csv_b64 = base64.b64encode(csv_bytes).decode("utf-8")
    csv_href = f"data:text/csv;charset=utf-8;base64,{csv_b64}"

    modal_id = "rgmMeasuresModal"
    download_svg, fullscreen_svg, close_svg = _icons_svg()

    table_normal = _build_measures_table_html(df_view, compact=True)
    table_modal = _build_measures_table_html(df_view, compact=False)

    html_block = (
        f'<div id="rgm-close"></div>'
        f'<div class="rgm-measures-card">'
        f'  <div class="rgm-measures-toolbar">'
        f'    <a class="rgm-tool-btn" href="{csv_href}" download="{_escape(csv_filename)}" title="CSV herunterladen" aria-label="CSV herunterladen">{download_svg}</a>'
        f'    <a class="rgm-tool-btn" href="#{modal_id}" title="Vollbild" aria-label="Vollbild">{fullscreen_svg}</a>'
        f"  </div>"
        f'  <div class="rgm-measures-scroll">{table_normal}</div>'
        f"</div>"
        f'<div id="{modal_id}" class="rgm-modal">'
        f'  <a href="#rgm-close" class="rgm-modal-backdrop" aria-label="Schließen"></a>'
        f'  <div class="rgm-modal-content" role="dialog" aria-modal="true">'
        f'    <div class="rgm-modal-header">'
        f'      <div class="rgm-modal-title">Geplante Maßnahmen (Vollbild)</div>'
        f'      <a class="rgm-modal-close" href="#rgm-close" title="Schließen" aria-label="Schließen">{close_svg}</a>'
        f"    </div>"
        f'    <div class="rgm-modal-body">{table_modal}</div>'
        f"  </div>"
        f"</div>"
    )
    st.markdown(html_block, unsafe_allow_html=True)

def _render_dual_plot_cards(
    fig_left,
    title_left: str,
    filename_left: str,
    fig_right,
    title_right: str,
    filename_right: str,
) -> None:
    """Zwei Plotly-Radar-Cards in EINEM components.html (stabil volle Breite, sauber responsiv)."""
    if fig_left is None and fig_right is None:
        st.info("Keine Daten vorhanden.")
        return

    dark = bool(st.session_state.get("dark_mode", False))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"
    card_bg = "#111827" if dark else "#ffffff"
    font_color = "rgba(255,255,255,0.92)" if dark else "#111111"
    muted = "rgba(255,255,255,0.70)" if dark else "rgba(0,0,0,0.60)"

    toolbar_bg = "rgba(17,24,39,0.85)" if dark else "rgba(255,255,255,0.92)"
    toolbar_hover = "rgba(202,116,6,0.25)" if dark else "rgba(202,116,6,0.14)"
    icon_green = "#2f9e44"

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

    # Farben für Mini-Legenden (pro Card)
    l_ist = _trace_color(fig_left, 0, "#1f77b4")
    l_soll = _trace_color(fig_left, 1, "#ff7f0e")
    r_ist = _trace_color(fig_right, 0, "#1f77b4")
    r_soll = _trace_color(fig_right, 1, "#ff7f0e")

    fig_left_json = "null" if fig_left is None else fig_left.to_json()
    fig_right_json = "null" if fig_right is None else fig_right.to_json()

    # Initialhöhe großzügig (JS setzt danach exakt)
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
      --plotH: 520px; /* wird per JS gesetzt */
    }}

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

    /* größere Hitbox ohne Layout-Verschiebung */
    .rgm-swatch-toggle::before{{
      content: "";
      position: absolute;
      left: -10px;
      right: -10px;
      top: -8px;
      bottom: -8px;
      background: transparent;
    }}

    /* optionaler Zustand: "aus" (nur Strich matter) */
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

    .rgm-scale-wrap{{
      display:flex;
      justify-content:center;
      margin-top: 10px;
      padding-bottom: 2px;
    }}

    .rgm-scale-box{{
      padding: 8px 14px;
      border: 1px solid {border};
      border-radius: 10px;
      background: {card_bg};
      color: {font_color};
      font-size: 14px;
      line-height: 1.4;
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: center;
    }}

    .rgm-scale-label{{ font-weight: 700; }}
    .rgm-scale-num{{ color: #d62728; font-weight: 800; }}

  </style>
</head>

<body>
  <div class="rgm-grid">
    <div id="cardL" class="rgm-card">
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

    <div id="cardR" class="rgm-card">
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
      const topGap = 12 * scale;     // y = yTop + topGap
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

      // 1) Wunschbreite: Textbreite + Padding (damit Box "an Text" passt)
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

      // 2) Wrapping simulieren => Zeilenanzahl
      const avail = boxW - 2 * pad;

      let lines = 1;
      let cx = labelW + 14 * scale; // nach "Legende:"

      for (const [num, txt] of items) {{
        ctx.font = fontNum;
        const nW = ctx.measureText(num).width;

        ctx.font = fontTail;
        const tail = ` - ${{txt}}`;
        const tailW = ctx.measureText(tail).width;

        const itemW = nW + (2 * scale) + tailW + (18 * scale);

        if (cx + itemW > avail) {{
          lines += 1;
          cx = itemW;     // neue Zeile beginnt bei pad, dann + itemW
        }} else {{
          cx += itemW;
        }}
      }}

      // 3) Höhe an Zeilen anpassen (mit etwas Luft unten)
      // Erste Baseline liegt bei pad + 22*scale, pro extra Zeile +lineStep
      const lastBaseline = pad + (22 * scale) + (lines - 1) * lineStep;
      const bottomExtra = 12 * scale; // etwas "Descent"-Luft
      const boxH = Math.max(64 * scale, lastBaseline + bottomExtra + pad);

      // Gesamthöhe, die drawScaleLegend belegt (topGap + boxH + bottomGap)
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

      // Box
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

      // "Legende:"
      ctx.font = m.fonts.fontLabel;
      ctx.fillStyle = EXPORT_TEXT;
      const label = "Legende:";
      ctx.fillText(label, cx, cy);
      cx += ctx.measureText(label).width + 14 * scale;

      const maxX = x + boxW - pad;

      for (const [num, txt] of items) {{
        // num
        ctx.font = m.fonts.fontNum;
        ctx.fillStyle = EXPORT_RED;
        const nW = ctx.measureText(num).width;

        // tail
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
      return m.totalH; // exakt belegte Höhe
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

      // Title
      ctx.save();
      ctx.fillStyle = EXPORT_TEXT;
      ctx.font = (900) + " " + (22 * scale) + "px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif";
      ctx.fillText(title || "", x, y);

      // Mini legend (lines)
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
        // colored line
        ctx.fillStyle = it.color;
        ctx.fillRect(cx, yLeg - lineH + 2 * scale, lineW, lineH);

        cx += lineW + 14 * scale;

        // label
        ctx.fillStyle = EXPORT_TEXT;
        ctx.fillText(it.label, cx, yLeg);

        cx += ctx.measureText(it.label).width + 32 * scale;
      }}

      ctx.restore();

      // Fixed header height
      return 120 * scale;
    }}


    async function exportCardCompositePNG(cardEl, filename, hideToolbar=true, scale=2) {{
      // WICHTIG: Export-Auflösung unabhängig von Card/Viewport
      const PLOT_H = 1200;
      const PLOT_W = Math.round(PLOT_H * 1.5);
      const PLOT_SCALE = Math.max(2, Math.min(3, Number(scale) || 3)); // 2..3

      if (!cardEl) return;

      const plotRoot = cardEl.querySelector(".js-plotly-plot");
      if (!plotRoot || typeof Plotly === "undefined") {{
        return;
      }}

      // Titel + Farben aus DOM lesen (immer konsistent mit UI)
      const title = (cardEl.querySelector(".rgm-title")?.textContent || "").trim();
      const sw = cardEl.querySelectorAll(".rgm-swatch-toggle");
      const istCol = sw[0] ? getComputedStyle(sw[0]).backgroundColor : "#1f77b4";
      const sollCol = sw[1] ? getComputedStyle(sw[1]).backgroundColor : "#ff7f0e";

      if (hideToolbar) cardEl.classList.add("rgm-capture-hide-toolbar");

      try {{
        // 1) Plotly rendert ein "sauberes" PNG in fixer Größe (nicht abhängig von DOM)
        const dataUrl = await Plotly.toImage(plotRoot, {{
          format: "png",
          width: PLOT_W,
          height: PLOT_H,
          scale: PLOT_SCALE
        }});

        const img = await loadImage(dataUrl);

        // 2) Composite bauen (Card-Look + Header + Plot + Skalen-Legende)
        const S = PLOT_SCALE;
        const PAD = 18 * S;
        const R = 16 * S;

        const HEADER_H = 110 * S;

        // Legend-Metriken VOR Canvas-Setup bestimmen (damit Höhe passt)
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

        // Hintergrund
        ctx.fillStyle = EXPORT_BG;
        ctx.fillRect(0, 0, out.width, out.height);

        // Card-Rahmen
        ctx.save();
        ctx.translate(PAD, PAD);
        ctx.fillStyle = EXPORT_BG;
        ctx.strokeStyle = EXPORT_BORDER;
        ctx.lineWidth = 2 * S;
        roundRect(ctx, 0, 0, cardW, cardH, R);
        ctx.fill();
        ctx.stroke();

        // Header
        drawHeader(ctx, cardW, 0, S, title, istCol, sollCol);

        // Plot
        ctx.drawImage(img, 0, HEADER_H);

        // Skalen-Legende unten
        drawScaleLegend(ctx, cardW, HEADER_H + img.height, S, legendMetrics);

        ctx.restore();

        // Download
        downloadDataUrl(out.toDataURL("image/png"), filename);

      }} finally {{
        if (hideToolbar) cardEl.classList.remove("rgm-capture-hide-toolbar");
      }}
    }}


    function setFrameHeight() {{
      const grid = document.querySelector(".rgm-grid");
      if (!grid) return;

      // NUR die tatsächlich sichtbare Höhe der Plot-Grid-Row
      const h = Math.ceil(grid.getBoundingClientRect().height);

      window.parent.postMessage({{
        isStreamlitMessage: true,
        type: "streamlit:setFrameHeight",
        height: h + 8   // kleiner Puffer
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

    function initOne(prefix, FIG, filename, titleText) {{
      let plotReady = false;
      const vis = [true, true];

      const card = document.getElementById(prefix === "L" ? "cardL" : "cardR");
      const head = document.getElementById(prefix === "L" ? "headL" : "headR");
      const plotDiv = document.getElementById(prefix === "L" ? "plotL" : "plotR");
      const btnDL = document.getElementById(prefix === "L" ? "dlL" : "dlR");
      const btnFS = document.getElementById(prefix === "L" ? "fsL" : "fsR");

      if (!card || !head || !plotDiv || !btnDL || !btnFS) {{
        return;
      }}

      if (!FIG) {{
        plotDiv.innerHTML = "<div style='color:{muted}; padding: 12px;'>Keine Daten</div>";
        setTimeout(setFrameHeight, 60);
        return;
      }}

      const LAYOUT = normalizeLayout(FIG.layout);

      // --- Baseline sichern (für Restore nach Fullscreen/Export) ---
      const BASE_MARGIN = Object.assign({{ l: 18, r: 18, t: 10, b: 18 }}, (LAYOUT.margin || {{}}));
      const BASE_DOMAIN = (LAYOUT.polar && LAYOUT.polar.domain)
        ? JSON.parse(JSON.stringify(LAYOUT.polar.domain))
        : {{ x: [0, 1], y: [0, 1] }};


      const BASE_ANG_TICK = (((LAYOUT.polar || {{}}).angularaxis || {{}}).tickfont || {{}}).size || 10;
      const BASE_RAD_TICK = (((LAYOUT.polar || {{}}).radialaxis || {{}}).tickfont || {{}}).size || 10;


      let lastFs = false;

      // --- Fullscreen: Radar etwas "kleiner" (mehr Rand + Domain einziehen), danach zurück ---
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

      // --- Helper: Layout-Objekt für Restore (normal vs. fullscreen) ---
      function relayoutObjForState(isFs) {{
        if (isFs) {{
          return {{
            "margin.l": Math.max(60, BASE_MARGIN.l),
            "margin.r": Math.max(60, BASE_MARGIN.r),
            "margin.t": Math.max(40, BASE_MARGIN.t),
            "margin.b": Math.max(60, BASE_MARGIN.b),
            "polar.domain.x": [0.08, 0.92],
            "polar.domain.y": [0.08, 0.92],
          }};
        }}
        return {{
          "margin.l": BASE_MARGIN.l,
          "margin.r": BASE_MARGIN.r,
          "margin.t": BASE_MARGIN.t,
          "margin.b": BASE_MARGIN.b,
          "polar.domain.x": BASE_DOMAIN.x,
          "polar.domain.y": BASE_DOMAIN.y,
        }};
      }}

      // --- Export: "Netz minimal kleiner" (nur für Download) ---
      const EXPORT_LAYOUT = {{
        "margin.l": Math.max(70, BASE_MARGIN.l),
        "margin.r": Math.max(70, BASE_MARGIN.r),
        "margin.t": Math.max(52, BASE_MARGIN.t),
        "margin.b": Math.max(72, BASE_MARGIN.b),
        "polar.domain.x": [0.07, 0.93],
        "polar.domain.y": [0.07, 0.93],
      }};

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

        // Fullscreen: Höhe = Viewport - Header
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

      // Klick nur auf dem farbigen Strich
      card.querySelectorAll(".rgm-swatch-toggle").forEach((swatch) => {{
        const i = Number(swatch.dataset.trace || "0");

        swatch.addEventListener("click", (e) => {{
          e.stopPropagation();
          toggleTrace(i, swatch);
        }});

        // Tastatur (Enter/Space)
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
            // Margins deutlich kleiner als vorher (140 war zu viel)
            "margin.l": Math.max(BASE_MARGIN.l, 90),
            "margin.r": Math.max(BASE_MARGIN.r, 90),
            "margin.t": Math.max(BASE_MARGIN.t, 50),
            "margin.b": Math.max(BASE_MARGIN.b, 90),

            // Radar weiter nach außen => Netz größer
            "polar.domain.x": [0.04, 0.96],
            "polar.domain.y": [0.04, 0.96],

            // Export-Schrift klar größer
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

      function sleep(ms) {{ return new Promise(r => setTimeout(r, ms)); }}

      btnDL.addEventListener("click", async () => {{
        if (!plotReady) return;

        try {{
          applyExportBoost(true);
          await sleep(120);
          safeResize(plotDiv);
          await sleep(120);

          // Export immer in "Fullscreen-Qualität" (unabhängig vom Viewport)
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

      // Robust gegen Sidebar-Toggle / Layout-Changes im Parent:
      const rootRO = new ResizeObserver(() => {{
        requestAnimationFrame(() => syncSizes());
      }});
      rootRO.observe(document.documentElement);

      window.addEventListener("resize", () => setTimeout(syncSizes, 80));
      document.addEventListener("fullscreenchange", () => setTimeout(syncSizes, 120));
    }}
    initOne("L", FIG_L, "{filename_left}", {title_left!r});
    initOne("R", FIG_R, "{filename_right}", {title_right!r});

  </script>
</body>
</html>
"""
    components.html(html_doc, height=initial_height, scrolling=True, width=1200)



def main() -> None:
    init_session_state()
    _inject_gesamtuebersicht_css()

    st.title("Gesamtübersicht")
    st.caption(
        "Zusammenfassung der Angaben zur Erhebung, visualisierte Ergebnisse und geplante Maßnahmen."
    )
    st.markdown("---")

    model = load_model_config()
    answers = get_answers()
    global_target = float(st.session_state.get("global_target_level", 3.0))
    dim_targets = st.session_state.get("dimension_targets", {}) or {}
    priorities = st.session_state.get("priorities", {}) or {}
    meta = st.session_state.get("meta", {}) or {}

    df_raw = build_overview_table(
        model=model,
        answers=answers,
        global_target_level=global_target,
        per_dimension_targets=dim_targets,
        priorities=priorities,
    )

    if df_raw is None or df_raw.empty:
        st.info("Noch keine Ergebnisse vorhanden – bitte zuerst die Erhebung durchführen.")
        return

    df_report = _clean_overview_df(df_raw)

    # 1) Angaben zur Erhebung
    a1, a2 = st.columns(2)
    with a1:
        st.write(f"**Name der Organisation:** {meta.get('org','') or '-'}")
        st.write(f"**Bereich:** {meta.get('area','') or '-'}")
        st.write(f"**Erhebung durchgeführt von:** {meta.get('assessor','') or '-'}")
    with a2:
        st.write(f"**Datum der Durchführung:** {meta.get('date_str','') or '-'}")
        st.write(f"**Angestrebtes Ziel:** {meta.get('target_label','') or '-'}")
        st.write(f"**Soll-Niveau (global):** {float(global_target):.1f}")

    st.markdown("")
    n_answered = _kpi_block(df_report)

    if n_answered == 0:
        st.warning("Noch keine Dimensionen bewertet.")
        if st.button("Zur Erhebung", type="primary", use_container_width=True):
            st.session_state["nav_request"] = "Erhebung"
            st.rerun()

    # 2) Graphen
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="rgm-section-title">Visualisiertes Ergebnis der Reifegraderhebung</div>',
        unsafe_allow_html=True,
    )

    dark = bool(st.session_state.get("dark_mode", False))
    
    def tune_plotly(fig):
        """Einheitliches Theme + etwas kompaktere Margins, damit das Radar größer wirkt."""
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
            # kompakter => Radar größer
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
    

    # --- Radar-Plots ---
    fig_td = tune_plotly(radar_ist_soll(df_raw, "TD", "TD-Dimensionen", dark=dark))
    fig_og = tune_plotly(radar_ist_soll(df_raw, "OG", "OG-Dimensionen", dark=dark))

    _render_dual_plot_cards(
        fig_left=fig_td,
        title_left="TD-Dimensionen",
        filename_left="reifegrad_radar_td",
        fig_right=fig_og,
        title_right="OG-Dimensionen",
        filename_right="reifegrad_radar_og",
    )

    _scale_legend_centered()

    # 3) Maßnahmen
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rgm-section-title">Geplante Maßnahmen</div>', unsafe_allow_html=True)

    df_export = df_results_for_export(df_report)
    m = df_export.copy()
    if "Gap" in m.columns:
        m["Gap"] = pd.to_numeric(m["Gap"], errors="coerce")

    # Verantwortlich sicherstellen/mappen (kommt aus priorities)
    if "Verantwortlich" not in m.columns:
        m["Verantwortlich"] = ""

    code_col = _pick_first_col(m, ["Kürzel", "Kuerzel", "code", "Code"])
    if code_col is not None:

        def _resp_for_code(code: str) -> str:
            try:
                return str(priorities.get(str(code), {}).get("responsible", "") or "")
            except Exception:
                return ""

        mapped = m[code_col].astype(str).map(_resp_for_code).fillna("")
        m["Verantwortlich"] = m["Verantwortlich"].astype(str).fillna("")
        m.loc[m["Verantwortlich"].str.strip().eq(""), "Verantwortlich"] = mapped

    need = m["Gap"].fillna(-1) > 0 if "Gap" in m.columns else pd.Series([True] * len(m))

    show_all = st.checkbox("Alle anzeigen (inkl. ohne Handlungsbedarf)", value=False)
    prio_filter = st.multiselect(
            "Priorität filtern",
            ["A (hoch)", "B (mittel)", "C (niedrig)"],
            default=[],
            placeholder="Prioritäten auswählen …",
        )

    filtered = m.copy() if show_all else m[need].copy()
    if prio_filter and "Priorität" in filtered.columns:
        filtered = filtered[filtered["Priorität"].isin(prio_filter)].copy()

    if filtered.empty:
        st.info("Keine Einträge passend zur aktuellen Auswahl.")
    else:
        # -----------------------------
        # Sortierung: Dimension (TD->OG) dann Priorität (A->B->C->leer) dann Gap
        # -----------------------------

        # 1) Priorität-Rang (A hoch zuerst, dann B, C, dann leer/alles andere)
        prio_rank = {"A (hoch)": 0, "B (mittel)": 1, "C (niedrig)": 2}
        if "Priorität" in filtered.columns:
            prio_clean = filtered["Priorität"].astype(str).fillna("").str.strip()
            filtered["_prio_rank"] = prio_clean.map(lambda x: prio_rank.get(x, 9))
        else:
            filtered["_prio_rank"] = 9

        # 2) Dimension-Rang (TD vor OG)
        # Dimension robust aus Kürzel/Code ableiten (z.B. "TD1.2", "OG3.1")
        dim_rank = {"TD": 0, "OG": 1}
        code_col2 = _pick_first_col(filtered, ["Kürzel", "Kuerzel", "code", "Code"])
        if code_col2 is not None:
            # Extrahiere Prefix "TD"/"OG" am Anfang
            dim = (
                filtered[code_col2]
                .astype(str)
                .fillna("")
                .str.strip()
                .str.upper()
                .str.extract(r"^(TD|OG)")[0]
                .fillna("")
            )
            filtered["_dim_rank"] = dim.map(lambda x: dim_rank.get(x, 9))
            filtered["_code_sort"] = (
                filtered[code_col2].astype(str).fillna("").str.strip()
            )
        else:
            filtered["_dim_rank"] = 9
            filtered["_code_sort"] = ""

        # 3) Gap-Sort (größeres Gap zuerst), falls vorhanden
        filtered["_gap_sort"] = (
            pd.to_numeric(filtered["Gap"], errors="coerce").fillna(-1)
            if "Gap" in filtered.columns
            else 0
        )

        # Finale Sortierung
        filtered = filtered.sort_values(
            ["_dim_rank", "_prio_rank", "_gap_sort", "_code_sort"],
            ascending=[True, True, False, True],
        )

        cols = [
            "Priorität",
            "Kürzel",
            "Themenbereich",
            "Ist-Reifegrad",
            "Soll-Reifegrad",
            "Gap",
            "Maßnahme",
            "Verantwortlich",
            "Zeitraum",
        ]
        cols = [c for c in cols if c in filtered.columns]
        view = filtered[cols].copy()

        # Zahlen hübsch formatieren
        for c in ["Ist-Reifegrad", "Soll-Reifegrad", "Gap"]:
            if c in view.columns:
                view[c] = pd.to_numeric(view[c], errors="coerce").apply(
                    lambda x: "" if x != x else f"{float(x):.2f}".rstrip("0").rstrip(".")
                )

        _render_measures_block(view, csv_filename="geplante_massnahmen.csv")

    # 4) Export
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)

    pdf_bytes = None
    pdf_error = None
    try:
        meta_pdf = dict(meta)
        meta_pdf["global_target"] = f"{float(global_target):.1f}"
        pdf_bytes = make_pdf_bytes(meta=meta_pdf, df_raw=df_raw)
    except Exception as e:
        pdf_error = str(e)

    if pdf_bytes is not None:
      st.download_button(
          "PDF-Bericht herunterladen",
          data=pdf_bytes,
          file_name="reifegrad_gesamtuebersicht.pdf",
          mime="application/pdf",
          use_container_width=True,
      )
    else:
        st.error(f"PDF-Export nicht verfügbar: {pdf_error}")


if __name__ == "__main__":
    main()
