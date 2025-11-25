# pages/01_Erhebung.py
import streamlit as st

from core.state import init_session_state
from core.model_loader import load_model_config


def render_dimension_block(dimension: dict):
    """
    Zeichnet einen Block für eine Dimension:
    - Beschreibung
    - Soll-Reifegrad (Slider)
    - Fragen zu allen Levels
    """
    code = dimension["code"]
    name = dimension["name"]
    description = dimension.get("description", "")

    with st.expander(f"{code} – {name}", expanded=False):
        if description:
            st.markdown(description)

        # Soll-Reifegrad: Dimension kann vom globalen Ziel abweichen
        dim_targets = st.session_state.dimension_targets
        current_default = dim_targets.get(code, st.session_state.global_target_level)

        target = st.slider(
            "Ziel-Reifegrad für diese Dimension",
            min_value=1.0,
            max_value=5.0,
            step=0.5,
            value=float(current_default),
            key=f"target_{code}",
        )
        st.session_state.dimension_targets[code] = target

        st.markdown("---")
        st.markdown("**Bewertung der Aussagen:** 1 = trifft gar nicht zu, 5 = trifft voll zu")

        # Fragen pro Level anzeigen
        for level in dimension["levels"]:
            level_no = level["level_number"]
            level_name = level["name"]

            st.markdown(f"### Stufe {level_no}: {level_name}")

            for q in level.get("questions", []):
                q_id = q["id"]
                q_text = q["text"]

                value = st.slider(
                    q_text,
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"answer_{q_id}",
                )
                st.session_state.answers[q_id] = value


def main():
    init_session_state()
    config = load_model_config()

    st.title("Erhebung – Reifegrad Technische Dokumentation")

    st.markdown(
        """
Bitte bewerten Sie die folgenden Aussagen zu den einzelnen Dimensionen.
Die Einschätzung erfolgt auf einer Skala von **1 (trifft gar nicht zu)** bis **5 (trifft voll zu)**.
"""
    )

    # Option: globaler Ziel-Reifegrad
    st.sidebar.header("Globale Einstellungen")
    global_target = st.sidebar.slider(
        "Globaler Ziel-Reifegrad",
        min_value=1.0,
        max_value=5.0,
        step=0.5,
        value=float(st.session_state.global_target_level),
    )
    st.session_state.global_target_level = global_target

    # Dimensionen aus der JSON-Datei
    dimensions = config.get("dimensions", [])

    # Optional: Filter nach Kategorie (OG / TD)
    categories = sorted({d["category"] for d in dimensions})
    selected_categories = st.multiselect(
        "Anzuzeigende Kategorien",
        options=categories,
        default=categories,
    )

    for dim in dimensions:
        if dim["category"] not in selected_categories:
            continue
        render_dimension_block(dim)

    st.markdown("---")
    st.success("Die Antworten werden nur in dieser Sitzung gehalten und **nicht** dauerhaft gespeichert.")

    st.markdown(
        "Die Auswertung erfolgt im Tab **„Dashboard“**. "
        "Dort sehen Sie Radar-Diagramm und Übersichtstabelle."
    )


if __name__ == "__main__":
    main()
