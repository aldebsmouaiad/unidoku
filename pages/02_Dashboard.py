# pages/02_Dashboard.py
import streamlit as st

from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.charts import radar_ist_soll
from core.state import init_session_state


def get_answers():
    # Antworten aus der Session holen (falls noch nicht vorhanden: leeres Dict)
    return st.session_state.get("answers", {})


def main():
    # Session-State initialisieren (answers, global_target_level, dimension_targets, ...)
    init_session_state()

    st.title("Dashboard – Gesamtübersicht")

    # Modell laden (aus data/models/niro_td_model.json)
    model = load_model_config()

    answers = get_answers()
    global_target = st.session_state.get("global_target_level", 3.0)
    dim_targets = st.session_state.get("dimension_targets", {})
    priorities = st.session_state.get("priorities", {})

    # Übersichtstabelle (eine Zeile pro Dimension)
    df = build_overview_table(
        model=model,
        answers=answers,
        global_target_level=global_target,
        per_dimension_targets=dim_targets,
        priorities=priorities,
    )

    st.subheader("Visualisierte Reifegrade")

    col1, col2 = st.columns(2)

    with col1:
        fig_td = radar_ist_soll(df, category="TD", title="TD-Dimensionen")
        if fig_td:
            st.plotly_chart(fig_td, use_container_width=True)
        else:
            st.info("Noch keine TD-Daten vorhanden – bitte zuerst die Erhebung ausfüllen.")

    with col2:
        fig_og = radar_ist_soll(df, category="OG", title="OG-Dimensionen")
        if fig_og:
            st.plotly_chart(fig_og, use_container_width=True)
        else:
            st.info("Noch keine OG-Daten vorhanden – bitte zuerst die Erhebung ausfüllen.")

    st.subheader("Ergebnis in Tabellenform")
    if df.empty:
        st.info("Noch keine Ergebnisse vorhanden.")
    else:
        st.dataframe(
            df[
                [
                    "code",
                    "name",
                    "category",
                    "ist_level",
                    "target_level",
                    "gap",
                    "priority",
                    "action",
                    "timeframe",
                ]
            ],
            use_container_width=True,
        )


# Nur wenn diese Datei direkt mit `streamlit run pages/02_Dashboard.py`
# gestartet wird – NICHT beim Import aus app.py:
if __name__ == "__main__":
    main()
