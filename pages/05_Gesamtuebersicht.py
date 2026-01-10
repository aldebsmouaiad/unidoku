# /workspaces/unidoku/pages/05_Gesamtuebersicht.py
from __future__ import annotations

import base64
import html
from typing import Optional

import pandas as pd
import streamlit as st

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
    """Gesamtübersicht-Design wie Dashboard + Dark/Light Tokens + Plotly-Modebar + Measures-Table + Modal robust."""
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

    modebar_bg = "rgba(17,24,39,0.85)" if dark else "rgba(255,255,255,0.92)"
    modebar_hover = "rgba(202,116,6,0.25)" if dark else "rgba(202,116,6,0.14)"

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
    margin: 26px 0 18px 0;
  }}
  .rgm-section-title {{
    font-weight: 850;
    font-size: 18px;
    margin: 0 0 12px 0;
    color: var(--rgm-text);
  }}

  /* =========================
     Plotly Card + Modebar
     ========================= */
  div[data-testid="stPlotlyChart"] {{
    background: var(--rgm-card-solid);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    box-shadow: {shadow};
    padding: 12px 12px 10px 12px;
    margin-top: 12px;
    overflow: hidden;
  }}
  div[data-testid="stPlotlyChart"] .js-plotly-plot .modebar {{
    top: 10px !important;
    right: 10px !important;
    z-index: 50 !important;
  }}
  div[data-testid="stPlotlyChart"] .modebar {{
    background: transparent !important;
  }}
  div[data-testid="stPlotlyChart"] .modebar-group {{
    background: {modebar_bg} !important;
    border: 1px solid var(--rgm-border) !important;
    border-radius: 10px !important;
    padding: 2px 4px !important;
    box-shadow: 0 10px 22px rgba(0,0,0,0.25) !important;
    backdrop-filter: blur(8px);
    margin: 0 !important;
  }}
  div[data-testid="stPlotlyChart"] .modebar-btn path {{
    fill: var(--rgm-text) !important;
  }}
  div[data-testid="stPlotlyChart"] .modebar-btn:hover {{
    background: {modebar_hover} !important;
    border-radius: 8px !important;
  }}

  button[kind="primary"] {{
    border-radius: 12px !important;
    font-weight: 850 !important;
  }}

  /* =========================
     Maßnahmen-Card + Toolbar (Modebar-Look)
     ========================= */
  .rgm-measures-card {{
    position: relative;
    --rgm-measures-toolbar-space: 44px;
    padding-top: var(--rgm-measures-toolbar-space); /* Toolbar-Platz außerhalb vom Scrollbereich */
    background: var(--rgm-card-solid);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    box-shadow: {shadow};
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
    background: {modebar_bg};
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
    color: var(--rgm-text);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }}
  a.rgm-tool-btn:hover {{
    background: {modebar_hover};
  }}
  .rgm-icon {{
    width: 18px;
    height: 18px;
    display: block;
  }}

  .rgm-measures-scroll {{
    max-height: calc(420px - var(--rgm-measures-toolbar-space)); /* gleiche Gesamthöhe wie vorher */
    overflow: auto;
    padding-top: 0; /* wichtig: kein Padding im Scrollport */
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
    box-shadow: 0 1px 0 var(--rgm-df-grid); /* klare Trennung zum Inhalt */
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

  /* Clamp NUR über inneres DIV (niemals auf <td>, sonst Layout-Bugs) */
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
     Vollbild-Modal (sauber, ohne Code-Text, Close klickbar)
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

  /* Close wie Modebar (und NICHT unter Streamlit-3-Punkte) */
  a.rgm-modal-close {{
    width: 40px;
    height: 34px;
    border-radius: 10px;
    border: 1px solid var(--rgm-border);
    background: {modebar_bg};
    color: var(--rgm-text);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }}
  a.rgm-modal-close:hover {{
    background: {modebar_hover};
  }}

  .rgm-modal-body {{
    padding-top: 0px; /* default */
    height: calc(100% - 56px);
    overflow: auto;
    background: var(--rgm-card-solid);
  }}

  /* =========================
   Modal: Sticky Header + Separator (wie Card)
   ========================= */
    .rgm-modal-body table.rgm-measures-table thead th{{
      position: sticky;
      top: 0;
      z-index: 20; /* über Body-Inhalt */
      background-color: var(--rgm-df-header) !important;
      background-image: none !important;
      opacity: 1 !important;
      border-bottom: 1px solid var(--rgm-df-grid) !important;
      box-shadow: 0 1px 0 var(--rgm-df-grid); /* schöner Separator */
    }}

    /* Optional: leichter Header-„Plate“-Effekt im Modal beim Scrollen */
    .rgm-modal-body table.rgm-measures-table thead{{
      position: relative;
      z-index: 21;
    }}


  /* Im Vollbild keine Clamps – alles sichtbar */
  .rgm-measures-full .rgm-cell {{
    display: block;
  }}

  /* Im Vollbild horizontal scrollen, falls nötig */
  .rgm-modal-body table.rgm-measures-table {{
    min-width: 1180px;
  }}

  /* Mobile */
  @media (max-width: 900px) {{
    .rgm-modal-content {{ inset: 10px; }}
    .rgm-modal-body table.rgm-measures-table {{ min-width: 980px; }}
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

    if n_answered:
        avg_ist = float(pd.to_numeric(d_ans["ist_level"], errors="coerce").mean())
        avg_soll = float(pd.to_numeric(d_ans["target_level"], errors="coerce").mean())
        max_gap = float(pd.to_numeric(d_ans["gap"], errors="coerce").max())
    else:
        avg_ist = 0.0
        avg_soll = float(
            pd.to_numeric(d.get("target_level"), errors="coerce").dropna().mean()
        ) if "target_level" in d.columns else 0.0
        max_gap = 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Dimensionen", f"{n_total}")
    c2.metric("Bewertet", f"{n_answered} / {n_total}")
    c3.metric("Handlungsbedarf (Gap > 0)", f"{n_need}")
    c4.metric("Ø Ist / Ø Soll", f"{avg_ist:.2f} / {avg_soll:.2f}")
    c5.metric("Max. Gap", f"{max_gap:.2f}")

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


def _measures_icons_svg() -> tuple[str, str, str]:
    """(download_svg, fullscreen_svg, close_svg) – stroke=currentColor, damit Dark/Light automatisch passt."""
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

    # feste, einheitliche Spaltenbreiten (professionell & stabil)
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

    colgroup = "".join(f'<col style="width:{int(width_map.get(c, 180))}px;">' for c in cols)
    thead = "".join(f"<th>{_escape(c)}</th>" for c in cols)

    # Wrap + (im Compact) line-clamp
    wrap_cols = {"Themenbereich", "Maßnahme", "Verantwortlich", "Zeitraum"}
    num_cols = {"Ist-Reifegrad", "Soll-Reifegrad", "Gap"}

    # Clamp-Strategie pro Spalte (nur compact)
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

    table_class = "rgm-measures-table rgm-measures-compact" if compact else "rgm-measures-table rgm-measures-full"

    return (
        f'<table class="{table_class}">'
        f"<colgroup>{colgroup}</colgroup>"
        f"<thead><tr>{thead}</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        f"</table>"
    )


def _render_measures_block(df_view: pd.DataFrame, csv_filename: str = "geplante_massnahmen.csv") -> None:
    """Geplante Maßnahmen: Dashboard-Downloadbutton + Modebar-Icons (Download + Vollbild) + robustes Modal."""
    csv_bytes = df_view.to_csv(index=False).encode("utf-8")

    

    # Toolbar-Icon Download (zusätzlich, optional)
    csv_b64 = base64.b64encode(csv_bytes).decode("utf-8")
    csv_href = f"data:text/csv;base64,{csv_b64}"

    modal_id = "rgmMeasuresModal"
    download_svg, fullscreen_svg, close_svg = _measures_icons_svg()

    table_normal = _build_measures_table_html(df_view, compact=True)
    table_modal = _build_measures_table_html(df_view, compact=False)

    # WICHTIG: keine Einrückung am Zeilenanfang (sonst Markdown-Codeblock-Artefakte)
    html_block = (
        f'<div id="rgm-close"></div>'
        f'<div class="rgm-measures-card">'
        f'  <div class="rgm-measures-toolbar">'
        f'    <a class="rgm-tool-btn" href="{csv_href}" download="{_escape(csv_filename)}" title="CSV herunterladen" aria-label="CSV herunterladen">{download_svg}</a>'
        f'    <a class="rgm-tool-btn" href="#{modal_id}" title="Vollbild" aria-label="Vollbild">{fullscreen_svg}</a>'
        f'  </div>'
        f'  <div class="rgm-measures-scroll">{table_normal}</div>'
        f'</div>'
        f'<div id="{modal_id}" class="rgm-modal">'
        f'  <a href="#rgm-close" class="rgm-modal-backdrop" aria-label="Schließen"></a>'
        f'  <div class="rgm-modal-content" role="dialog" aria-modal="true">'
        f'    <div class="rgm-modal-header">'
        f'      <div class="rgm-modal-title">Geplante Maßnahmen (Vollbild)</div>'
        f'      <a class="rgm-modal-close" href="#rgm-close" title="Schließen" aria-label="Schließen">{close_svg}</a>'
        f'    </div>'
        f'    <div class="rgm-modal-body">{table_modal}</div>'
        f'  </div>'
        f'</div>'
    )

    st.markdown(html_block, unsafe_allow_html=True)


def main() -> None:
    init_session_state()
    _inject_gesamtuebersicht_css()

    st.title("Gesamtübersicht")
    st.caption("Zusammenfassung der Angaben zur Erhebung, visualisierte Ergebnisse und geplante Maßnahmen.")
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

    # 2) Graphen wie Dashboard
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rgm-section-title">Visualisiertes Ergebnis der Reifegraderhebung</div>', unsafe_allow_html=True)

    dark = bool(st.session_state.get("dark_mode", False))

    plotly_cfg_base = {
        "displayModeBar": "hover",
        "displaylogo": False,
        "scrollZoom": False,
        "doubleClick": False,
        "editable": False,
        "responsive": True,
        "toImageButtonOptions": {"format": "png", "width": 1600, "height": 1000, "scale": 2},
        "modeBarButtonsToRemove": [
            "zoom2d", "pan2d", "select2d", "lasso2d",
            "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d",
            "hoverClosestCartesian", "hoverCompareCartesian",
            "toggleSpikelines",
            "hoverClosestPolar", "hoverComparePolar",
        ],
    }
    plotly_cfg_td = {
        **plotly_cfg_base,
        "toImageButtonOptions": {**plotly_cfg_base["toImageButtonOptions"], "filename": "reifegrad_radar_td"},
    }
    plotly_cfg_og = {
        **plotly_cfg_base,
        "toImageButtonOptions": {**plotly_cfg_base["toImageButtonOptions"], "filename": "reifegrad_radar_og"},
    }

    def tune_plotly(fig):
        if fig is None:
            return None
        bg = "#111827" if dark else "#ffffff"
        font_color = "rgba(255,255,255,0.92)" if dark else "#111111"
        grid = "rgba(255,255,255,0.14)" if dark else "rgba(0,0,0,0.10)"
        axis_line = "rgba(255,255,255,0.22)" if dark else "rgba(0,0,0,0.14)"
        legend_bg = "rgba(17,24,39,0.85)" if dark else "rgba(255,255,255,0.92)"
        legend_border = "rgba(255,255,255,0.18)" if dark else "rgba(0,0,0,0.12)"
        fig.update_layout(
            template="plotly_dark" if dark else "plotly_white",
            paper_bgcolor=bg,
            plot_bgcolor=bg,
            font=dict(color=font_color),
            margin=dict(l=30, r=30, t=55, b=30),
            legend=dict(bgcolor=legend_bg, bordercolor=legend_border, borderwidth=1, font=dict(color=font_color)),
        )
        fig.update_polars(
            bgcolor=bg,
            radialaxis=dict(gridcolor=grid, linecolor=axis_line, tickfont=dict(color=font_color)),
            angularaxis=dict(gridcolor=grid, linecolor=axis_line, tickfont=dict(color=font_color)),
        )
        return fig

    c1, c2 = st.columns(2)
    with c1:
        fig_td = tune_plotly(radar_ist_soll(df_raw, "TD", "TD-Dimensionen", dark=dark))
        if fig_td is not None:
            st.plotly_chart(fig_td, use_container_width=True, config=plotly_cfg_td)
        else:
            st.info("Keine TD-Daten vorhanden.")
    with c2:
        fig_og = tune_plotly(radar_ist_soll(df_raw, "OG", "OG-Dimensionen", dark=dark))
        if fig_og is not None:
            st.plotly_chart(fig_og, use_container_width=True, config=plotly_cfg_og)
        else:
            st.info("Keine OG-Daten vorhanden.")

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

    f1, f2 = st.columns([1.2, 1.0])
    with f1:
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
        prio_rank = {"A (hoch)": 0, "B (mittel)": 1, "C (niedrig)": 2, "": 9}
        if "Priorität" in filtered.columns:
            filtered["_prio_rank"] = filtered["Priorität"].map(lambda x: prio_rank.get(str(x), 9))
        else:
            filtered["_prio_rank"] = 9

        filtered["_gap_sort"] = filtered["Gap"].fillna(-1) if "Gap" in filtered.columns else 0
        filtered = filtered.sort_values(["_prio_rank", "_gap_sort"], ascending=[True, False])

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
    st.markdown('<div class="rgm-section-title">Export</div>', unsafe_allow_html=True)

    csv_bytes = make_csv_bytes(df_export)

    pdf_bytes = None
    pdf_error = None
    try:
        meta_pdf = dict(meta)
        meta_pdf["global_target"] = f"{float(global_target):.1f}"
        pdf_bytes = make_pdf_bytes(meta=meta_pdf, df_raw=df_raw)
    except Exception as e:
        pdf_error = str(e)

    ex1, ex2 = st.columns(2)
    with ex1:
        st.download_button(
            "CSV herunterladen",
            data=csv_bytes,
            file_name="reifegrad_gesamtuebersicht.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with ex2:
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
