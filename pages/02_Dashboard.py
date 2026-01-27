# pages/02_Dashboard.py
from __future__ import annotations

import streamlit as st

from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.charts import radar_ist_soll
from core.state import init_session_state

TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"


def _inject_dashboard_css() -> None:
    """Dashboard-UI (Hero/Divider/Cards) + Dark/Light + Plotly-Modebar sauber sichtbar."""
    dark = bool(st.session_state.get("dark_mode", False))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    header_bg = "rgba(255,255,255,0.08)" if dark else "rgba(127,127,127,0.10)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

    # Card/Typo
    card_bg = "rgba(255,255,255,0.05)" if dark else "rgba(255,255,255,1.00)"
    card_solid = "#111827" if dark else "#ffffff"  # SOLID für Fullscreen + Download korrekt
    text_color = "rgba(255,255,255,0.92)" if dark else "#111111"
    df_bg = "#0f172a" if dark else "#ffffff"
    df_header = "#111827" if dark else "#f3f4f6"
    df_grid = "rgba(255,255,255,0.10)" if dark else "rgba(0,0,0,0.10)"
    df_hover = "rgba(202,116,6,0.18)" if dark else "rgba(202,116,6,0.10)"
    df_text = "rgba(250,250,250,0.92)" if dark else "#111111"
    df_muted = "rgba(250,250,250,0.70)" if dark else "rgba(0,0,0,0.60)"


    # Modebar (Plotly)
    modebar_bg = "rgba(17,24,39,0.85)" if dark else "rgba(255,255,255,0.92)"
    modebar_hover = "rgba(202,116,6,0.25)" if dark else "rgba(202,116,6,0.14)"

    st.markdown(
        f"""
<style>
  /* =========================================================
     Tokens + Container
     ========================================================= */
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

  /* =========================================================
     Anchor-Link (Kettensymbol) robust ausblenden
     ========================================================= */
  a.anchor-link,
  a.header-anchor,
  a[data-testid="stHeaderLink"],
  a[aria-label="Anchor link"],
  a[data-testid="stMarkdownAnchorLink"],
  svg[data-testid="stMarkdownAnchorIcon"] {{
    display: none !important;
  }}

  /* =========================================================
     Leere "Pill"-Container entfernen (Element Toolbar)
     ========================================================= */
  div[data-testid="stElementToolbar"],
  div[data-testid="stElementToolbar"] * ,
  button[data-testid="stElementToolbarButton"] {{
    display: none !important;
  }}
  div[data-testid="stElementToolbar"] {{
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
  }}

  /* =========================================================
     HERO
     ========================================================= */
  .rgm-hero {{
    background: var(--rgm-card-bg);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    padding: 18px 18px 14px 18px;
    box-shadow: {shadow};
    margin-top: 6px;
  }}

  .rgm-h1 {{
    font-size: 30px;
    font-weight: 850;
    line-height: 1.15;
    margin: 0 0 6px 0;
    color: var(--rgm-text);
  }}

  .rgm-lead {{
    font-size: 15px;
    line-height: 1.75;
    color: var(--rgm-text);
    opacity: 0.92;
    margin: 0;
  }}

  .rgm-accent-line {{
    height: 3px;
    width: 96px;
    border-radius: 999px;
    margin: 10px 0 14px 0;
    background: linear-gradient(90deg, var(--rgm-td-blue), var(--rgm-og-orange));
  }}

  /* =========================================================
     Divider + Section-Titel
     ========================================================= */
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

  /* =========================================================
     "Cards" direkt auf Streamlit-Elemente
     ========================================================= */
  div[data-testid="stPlotlyChart"] {{
    background: var(--rgm-card-solid);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    box-shadow: {shadow};
    padding: 12px 12px 10px 12px;
    margin-top: 12px;
    overflow: hidden; /* darf bleiben, Modebar wird nach innen verschoben */
  }}

  div[data-testid="stDataFrame"] {{
    background: var(--rgm-card-solid);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    box-shadow: {shadow};
    padding: 12px;
    margin-top: 12px;
    overflow: hidden;
  }}

    /* =========================================================
     DataFrame (st.dataframe) – Darkmode/Lightmode Styling
     Funktioniert für neue Grid-Renderer + Fallback für HTML-Table
     ========================================================= */

  /* Container transparent lassen, aber innen das Grid einfärben */
  div[data-testid="stDataFrame"] .stDataFrame,
  div[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {{
    background: transparent !important;
  }}

  /* ---------
     MODERN GRID (roles) – robust in vielen Streamlit-Versionen
     --------- */
  div[data-testid="stDataFrame"] [role="grid"],
  div[data-testid="stDataFrame"] [role="grid"] * {{
    color: var(--rgm-df-text) !important;
  }}

  div[data-testid="stDataFrame"] [role="grid"] {{
    background: var(--rgm-df-bg) !important;
    border: 1px solid var(--rgm-df-grid) !important;
    border-radius: 10px !important;
  }}

  /* Header (Spaltennamen + Indexkopf) */
  div[data-testid="stDataFrame"] [role="columnheader"],
  div[data-testid="stDataFrame"] [role="rowheader"] {{
    background: var(--rgm-df-header) !important;
    border-bottom: 1px solid var(--rgm-df-grid) !important;
    font-weight: 700 !important;
    color: var(--rgm-df-text) !important;
  }}

  /* Zellen */
  div[data-testid="stDataFrame"] [role="gridcell"] {{
    background: var(--rgm-df-bg) !important;
    border-bottom: 1px solid var(--rgm-df-grid) !important;
    color: var(--rgm-df-text) !important;
  }}

  /* Hover */
  div[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {{
    background: var(--rgm-df-hover) !important;
  }}

  /* Scrollbar (Webkit) */
  div[data-testid="stDataFrame"] ::-webkit-scrollbar {{
    height: 10px;
    width: 10px;
  }}
  div[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb {{
    background: var(--rgm-df-grid);
    border-radius: 999px;
  }}
  div[data-testid="stDataFrame"] ::-webkit-scrollbar-track {{
    background: transparent;
  }}

  /* ---------
     FALLBACK: falls Streamlit als HTML-Table rendert
     --------- */
  div[data-testid="stDataFrame"] table {{
    background: var(--rgm-df-bg) !important;
    color: var(--rgm-df-text) !important;
  }}
  div[data-testid="stDataFrame"] thead th {{
    background: var(--rgm-df-header) !important;
    color: var(--rgm-df-text) !important;
    border-bottom: 1px solid var(--rgm-df-grid) !important;
  }}
  div[data-testid="stDataFrame"] tbody td {{
    background: var(--rgm-df-bg) !important;
    color: var(--rgm-df-text) !important;
    border-bottom: 1px solid var(--rgm-df-grid) !important;
  }}
  div[data-testid="stDataFrame"] tbody tr:hover td {{
    background: var(--rgm-df-hover) !important;
  }}



    /* =========================================================
     Ergebnis-Tabelle als HTML (dark-mode-fähig, sticky header)
     ========================================================= */
  .rgm-table-card {{
    background: var(--rgm-card-solid);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    box-shadow: 0 12px 28px rgba(0,0,0,0.40);
    overflow: hidden;
    margin-top: 12px;
  }}

  .rgm-table-scroll {{
    max-height: 420px;
    overflow: auto;
  }}

  table.rgm-table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--rgm-df-bg);
    color: var(--rgm-df-text);
    font-size: 14px;
  }}

  table.rgm-table thead th {{
  position: sticky;
  top: 0;
  z-index: 10;

  /* WICHTIG: opaker Header (kein Durchscheinen) */
  background-color: var(--rgm-df-header) !important;
  background-image: none !important;
  opacity: 1 !important;

  color: var(--rgm-df-text);
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--rgm-df-grid);
  font-weight: 800;
  white-space: nowrap;
  box-shadow: 0 1px 0 var(--rgm-df-grid);
}}


  table.rgm-table tbody td {{
    padding: 10px 12px;
    border-bottom: 1px solid var(--rgm-df-grid);
    color: var(--rgm-df-text);
    vertical-align: top;
  }}

  table.rgm-table tbody tr:hover td {{
    background: var(--rgm-df-hover);
  }}

  /* Zahlen rechtsbündig */
  table.rgm-table tbody td:nth-child(3),
  table.rgm-table tbody td:nth-child(4) {{
    text-align: right;
    font-variant-numeric: tabular-nums;
  }}

  /* Scrollbar */
  .rgm-table-scroll::-webkit-scrollbar {{ height: 10px; width: 10px; }}
  .rgm-table-scroll::-webkit-scrollbar-thumb {{
    background: var(--rgm-df-grid);
    border-radius: 999px;
  }}
  .rgm-table-scroll::-webkit-scrollbar-track {{ background: transparent; }}



  /* =========================================================
     Plotly Modebar: sichtbar + nicht abgeschnitten
     ========================================================= */

  /* Modebar nach innen (damit Symbole vollständig sichtbar sind) */
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

  /* Icons */
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

  @media (max-width: 900px) {{
    .rgm-h1 {{ font-size: 26px; }}
    .rgm-hero {{ padding: 16px; }}
    .rgm-divider {{ margin: 28px 0 18px 0; }}
    div[data-testid="stPlotlyChart"] .js-plotly-plot .modebar {{
      top: 8px !important;
      right: 8px !important;
    }}
  }}
</style>
        """,
        unsafe_allow_html=True,
    )


def get_answers() -> dict:
    """Antworten aus der Session holen (falls noch nicht vorhanden: leeres Dict)."""
    return st.session_state.get("answers", {}) or {}


def after_dash(text: str) -> str:
    """Gibt nur den Teil nach dem ersten '-' zurück (getrimmt)."""
    s = "" if text is None else str(text)
    return s.split("-", 1)[1].strip() if "-" in s else s.strip()


def main() -> None:
    init_session_state()
    _inject_dashboard_css()

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

    # -----------------------------
    # Plotly Config: Modebar nur Fullscreen + Download
    # Download soll "Fullscreen-Qualität" liefern -> große Exportgröße setzen
    # -----------------------------
    plotly_cfg_base = {
        "displayModeBar": "hover",
        "displaylogo": False,
        "scrollZoom": False,
        "doubleClick": False,
        "editable": False,
        "responsive": True,
        "toImageButtonOptions": {
            "format": "png",
            # große Exportfläche => wirkt wie Fullscreen-Export
            "width": 1600,
            "height": 1000,
            "scale": 2,
        },
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

    # -----------------------------
    # Plotly Styling: SOLID background (Fullscreen + PNG-Export korrekt)
    # -----------------------------
    dark = bool(st.session_state.get("dark_mode", False))

    def tune_plotly(fig):
        """Sicherer Dark/Light-Look für Anzeige + Fullscreen + PNG-Export (Radar = polar)."""
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
            legend=dict(
                bgcolor=legend_bg,
                bordercolor=legend_border,
                borderwidth=1,
                font=dict(color=font_color),
            ),
        )

        fig.update_polars(
            bgcolor=bg,
            radialaxis=dict(gridcolor=grid, linecolor=axis_line, tickfont=dict(color=font_color)),
            angularaxis=dict(gridcolor=grid, linecolor=axis_line, tickfont=dict(color=font_color)),
        )
        return fig

    # ---------- Radar-Diagramme ----------
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rgm-section-title">Radar-Diagramme</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        fig_td = radar_ist_soll(df, "TD", "TD-Dimensionen", dark=dark)
        if fig_td is not None:
            st.plotly_chart(fig_td, use_container_width=True, config=plotly_cfg_td)
        else:
            st.info("Noch keine TD-Daten vorhanden – bitte zuerst die Erhebung ausfüllen.")

    with col2:
        fig_og = radar_ist_soll(df, "OG", "OG-Dimensionen", dark=dark)
        if fig_og is not None:
            st.plotly_chart(fig_og, use_container_width=True, config=plotly_cfg_og)
        else:
            st.info("Noch keine OG-Daten vorhanden – bitte zuerst die Erhebung ausfüllen.")

    # Legende (dark-mode-fähig)
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
          .rgm-legend-box .rgm-num {
            color: #d62728 !important;
            font-weight: 700 !important;
          }
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

    # ---------- Ergebnis in Tabellenform ----------
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rgm-section-title">Ergebnis in Tabellenform</div>', unsafe_allow_html=True)

    if df is None or df.empty:
        st.info("Noch keine Ergebnisse vorhanden.")
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

        # Download (CSV) rechts über der Tabelle
        _, right = st.columns([0.72, 0.28])
        with right:
            st.download_button(
                label="Tabelle herunterladen (CSV)",
                data=df_view.to_csv(index=False).encode("utf-8"),
                file_name="ergebnis_tabelle.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_table_csv",
            )

        for c in ["Ist-Reifegrad", "Soll-Reifegrad"]:
            df_view[c] = df_view[c].apply(lambda x: "" if x != x else f"{float(x):.2f}".rstrip("0").rstrip("."))

        # als HTML-Tabelle rendern (dark-mode-fähig)
        table_html = df_view.to_html(index=False, classes="rgm-table", border=0, escape=True)

        st.markdown(
            f"""
            <div class="rgm-table-card">
              <div class="rgm-table-scroll">
                {table_html}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Navigation
    st.markdown("---")
    can_proceed = df is not None and not df.empty

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


if __name__ == "__main__":
    main()
