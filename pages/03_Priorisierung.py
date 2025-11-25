# pages/03_Priorisierung.py

import streamlit as st

from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.state import init_session_state


def get_answers():
    return st.session_state.get("answers", {})


def main():
    init_session_state()

    st.title("Priorisierung & Maßnahmenplanung")

    # Modell aus JSON laden
    model = load_model_config()

    answers = get_answers()
    global_target = st.session_state.get("global_target_level", 3.0)
    dim_targets = st.session_state.get("dimension_targets", {})
    priorities = st.session_state.get("priorities", {})

    st.write(
        "Legen Sie für jede Dimension fest, **wie wichtig** sie ist und "
        "welche **konkreten Maßnahmen** Sie angehen möchten."
    )

    df = build_overview_table(
        model=model,
        answers=answers,
        global_target_level=global_target,
        per_dimension_targets=dim_targets,
        priorities=priorities,
    )

    new_priorities = {}

    if df.empty:
        st.info("Noch keine Ergebnisse vorhanden – bitte zuerst die Erhebung durchführen.")
        return

    for _, row in df.iterrows():
        code = row["code"]
        name = row["name"]
        gap = row["gap"]

        st.markdown(f"### {code} – {name}")
        st.caption(f"Gap (Soll–Ist): **{gap:.2f}** Reifegradstufen")

        col1, col2, col3 = st.columns([1, 3, 2])

        # Bisherige Priorität vorbefüllen (falls vorhanden)
        prev = priorities.get(code, {})
        options = ["", "A (hoch)", "B (mittel)", "C (niedrig)"]
        try:
            default_index = options.index(prev.get("priority", ""))
        except ValueError:
            default_index = 0

        with col1:
            priority = st.selectbox(
                "Priorität",
                options=options,
                index=default_index,
                key=f"prio_{code}",
            )

        with col2:
            action = st.text_input(
                "Maßnahme",
                value=prev.get("action", ""),
                key=f"action_{code}",
                placeholder="z. B. Redaktionsleitfaden erstellen",
            )

        with col3:
            timeframe = st.text_input(
                "Zeitraum",
                value=prev.get("timeframe", ""),
                key=f"timeframe_{code}",
                placeholder="z. B. Q1/2026",
            )

        if priority or action or timeframe:
            new_priorities[code] = {
                "priority": priority,
                "action": action,
                "timeframe": timeframe,
            }

        st.markdown("---")

    if st.button("Priorisierungen übernehmen"):
        st.session_state["priorities"] = new_priorities
        st.success("Prioritäten und Maßnahmen wurden aktualisiert.")


if __name__ == "__main__":
    main()