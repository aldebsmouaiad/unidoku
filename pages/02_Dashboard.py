# /workspaces/unidoku/pages/02_Dashboard.py
from __future__ import annotations

import streamlit as st

from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.charts import radar_ist_soll
from core.state import init_session_state


def get_answers() -> dict:
    """Antworten aus der Session holen (falls noch nicht vorhanden: leeres Dict)."""
    return st.session_state.get("answers", {}) or {}


def after_dash(text: str) -> str:
    """Gibt nur den Teil nach dem ersten '-' zurück (getrimmt)."""
    s = "" if text is None else str(text)
    return s.split("-", 1)[1].strip() if "-" in s else s.strip()


def main() -> None:
    # Session-State initialisieren (answers, global_target_level, dimension_targets, ...)
    init_session_state()

    st.title("Dashboard")
    st.subheader("Visualisiertes Ergebnis der Reifegraderhebung:")

    # Modell laden (aus data/models/niro_td_model.json)
    model = load_model_config()

    answers = get_answers()
    global_target = float(st.session_state.get("global_target_level", 3.0))
    dim_targets = st.session_state.get("dimension_targets", {}) or {}
    priorities = st.session_state.get("priorities", {}) or {}

    # Übersichtstabelle (eine Zeile pro Dimension)
    df = build_overview_table(
        model=model,
        answers=answers,
        global_target_level=global_target,
        per_dimension_targets=dim_targets,
        priorities=priorities,
    )

    # Plotly-Config: Zoom/Reset deaktiviert, Hover bleibt aktiv
    plotly_cfg = {
        "displayModeBar": "hover",  # oder False, wenn du die Leiste komplett weg willst
        "displaylogo": False,
        "scrollZoom": False,        # Mausrad/Trackpad-Zoom aus
        "doubleClick": False,       # Double-Click Autoscale/Reset aus
        "editable": False,
        "responsive": True,
        "modeBarButtonsToRemove": [
            # häufige Interaktions-Buttons entfernen (auch wenn manche bei polar nicht erscheinen)
            "zoom2d", "pan2d", "select2d", "lasso2d",
            "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d",
        ],
        "toImageButtonOptions": {
            "format": "png",
            "filename": "reifegrad_radar",
            "scale": 2,
        },
    }

    col1, col2 = st.columns(2)

    with col1:
        fig_td = radar_ist_soll(df, category="TD", title="TD-Dimensionen")
        if fig_td is not None:
            st.plotly_chart(fig_td, use_container_width=True, config=plotly_cfg)
        else:
            st.info("Noch keine TD-Daten vorhanden – bitte zuerst die Erhebung ausfüllen.")

    with col2:
        fig_og = radar_ist_soll(df, category="OG", title="OG-Dimensionen")
        if fig_og is not None:
            st.plotly_chart(fig_og, use_container_width=True, config=plotly_cfg)
        else:
            st.info("Noch keine OG-Daten vorhanden – bitte zuerst die Erhebung ausfüllen.")

    # --- Skalen-Legende (horizontal, mittig, Zahlen rot) unter den Diagrammen ---
    st.markdown(
        """
        <style>
          .rgm-legend-wrap { display:flex; justify-content:center; margin-top: 10px; }
          .rgm-legend-box {
            padding: 8px 14px;
            border: 1px solid rgba(0,0,0,0.10);
            border-radius: 10px;
            background: rgba(255,255,255,0.90);
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

    st.subheader("Ergebnis in Tabellenform:")
    if df is None or df.empty:
        st.info("Noch keine Ergebnisse vorhanden.")
    else:
        # Nur die gewünschten Spalten anzeigen + umbenennen
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

    # -----------------------------
    # Navigation: Weiter zur Priorisierung
    # -----------------------------
    st.markdown("---")
    can_proceed = df is not None and not df.empty  # nur weiter, wenn Ergebnisse vorhanden sind

    if st.button(
        "Weiter zur Priorisierung",
        type="primary",
        use_container_width=True,
        disabled=not can_proceed,
    ):
        # optional: Rücksprung ermöglichen (wie im Glossar)
        st.session_state["nav_return_page"] = "Dashboard"
        st.session_state["nav_return_payload"] = {}

        # zentrale Navigation (wie in deinen anderen Seiten)
        st.session_state["nav_request"] = "Priorisierung"
        st.rerun()


if __name__ == "__main__":
    main()
