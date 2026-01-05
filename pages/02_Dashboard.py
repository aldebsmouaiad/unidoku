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
    """UI-Style (Abstand/Divider/Toolbar weg) + Dark-Mode-lesbar. Keine Logikänderung."""
    dark = bool(st.session_state.get("dark_mode", False))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    header_bg = "rgba(255,255,255,0.08)" if dark else "rgba(127,127,127,0.10)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

    # Dark-Mode Lesbarkeit
    card_bg = "rgba(255,255,255,0.05)" if dark else "rgba(255,255,255,1.00)"
    text_color = "rgba(255,255,255,0.92)" if dark else "#111111"

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
    --rgm-text: {text_color};
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
     Divider + Section-Titel (mit "Luft" wie Screenshot)
     ========================================================= */
  .rgm-divider {{
    height: 1px;
    width: 100%;
    background: var(--rgm-border);
    margin: 34px 0 22px 0; /* mehr Abstand wie gewünscht */
  }}

  .rgm-section-title {{
    font-weight: 850;
    font-size: 18px;
    margin: 0 0 14px 0;
    color: var(--rgm-text);
  }}

  /* =========================================================
     Cards
     ========================================================= */
  .rgm-card {{
    background: var(--rgm-card-bg);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    box-shadow: {shadow};
    padding: 12px 12px 10px 12px;
    margin-top: 12px;
  }}

  button[kind="primary"] {{
    border-radius: 12px !important;
    font-weight: 850 !important;
  }}

  @media (max-width: 900px) {{
    .rgm-h1 {{ font-size: 26px; }}
    .rgm-hero {{ padding: 16px; }}
    .rgm-card {{ padding: 10px 10px 8px 10px; }}
    .rgm-divider {{ margin: 28px 0 18px 0; }}
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

    plotly_cfg = {
        "displayModeBar": "hover",
        "displaylogo": False,
        "scrollZoom": False,
        "doubleClick": False,
        "editable": False,
        "responsive": True,
        "modeBarButtonsToRemove": [
            "zoom2d", "pan2d", "select2d", "lasso2d",
            "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d",
        ],
        "toImageButtonOptions": {"format": "png", "filename": "reifegrad_radar", "scale": 2},
    }

    # ---------- Radar-Diagramme (Divider + Abstand) ----------
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rgm-section-title">Radar-Diagramme</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="rgm-card">', unsafe_allow_html=True)
        fig_td = radar_ist_soll(df, category="TD", title="TD-Dimensionen")
        if fig_td is not None:
            st.plotly_chart(fig_td, use_container_width=True, config=plotly_cfg)
        else:
            st.info("Noch keine TD-Daten vorhanden – bitte zuerst die Erhebung ausfüllen.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="rgm-card">', unsafe_allow_html=True)
        fig_og = radar_ist_soll(df, category="OG", title="OG-Dimensionen")
        if fig_og is not None:
            st.plotly_chart(fig_og, use_container_width=True, config=plotly_cfg)
        else:
            st.info("Noch keine OG-Daten vorhanden – bitte zuerst die Erhebung ausfüllen.")
        st.markdown("</div>", unsafe_allow_html=True)

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

    # ---------- Ergebnis in Tabellenform (Divider + Abstand) ----------
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rgm-section-title">Ergebnis in Tabellenform</div>', unsafe_allow_html=True)

    st.markdown('<div class="rgm-card">', unsafe_allow_html=True)
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
        st.dataframe(df_view, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

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
