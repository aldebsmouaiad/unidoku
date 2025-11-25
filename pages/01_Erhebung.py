# pages/01_Erhebung.py
# Fragebogen für alle Dimensionen

import streamlit as st

from core.model_loader import load_model
from core.state import ensure_session_state, render_sidebar_meta
from core.scoring import ANSWER_OPTIONS, compute_results


def recompute_results():
    model = load_model()
    meta = st.session_state.meta
    df_dim, df_cat, overall = compute_results(
        model=model,
        answers=st.session_state.answers,
        global_target_level=meta["target_level"],
        dimension_targets=st.session_state.dimension_targets,
    )
    st.session_state.df_dim = df_dim
    st.session_state.df_cat = df_cat
    st.session_state.overall = overall


def main():
    ensure_session_state()
    meta = render_sidebar_meta()
    model = load_model()

    st.title("Erhebung – Fragebogen")

    st.markdown(
        """
Wähle eine Dimension aus und beantworte die zugehörigen Kontrollfragen.

Antwortskala:

- **Vollständig**
- **In den meisten Fällen**
- **In ein paar Fällen**
- **Gar nicht**
- **Nicht anwendbar**
"""
    )

    dim_labels = [f"{d.code} – {d.name}" for d in model.dimensions]
    dim_codes = [d.code for d in model.dimensions]

    selected = st.selectbox("Dimension auswählen", options=dim_labels)
    selected_code = dim_codes[dim_labels.index(selected)]
    dimension = next(d for d in model.dimensions if d.code == selected_code)

    st.markdown(f"### {dimension.code} – {dimension.name}")
    if dimension.description:
        st.info(dimension.description)

    # Optional: Dimension-spezifisches Zielniveau
    with st.expander("Individuelles Zielniveau für diese Dimension (optional)"):
        current_override = st.session_state.dimension_targets.get(dimension.code, None)
        use_override = st.checkbox(
            "Eigenes Ziel für diese Dimension setzen",
            value=current_override is not None,
        )
        if use_override:
            override_val = st.slider(
                "Ziel-Reifegrad (1–5)",
                1,
                5,
                value=int(current_override or meta["target_level"]),
            )
            st.session_state.dimension_targets[dimension.code] = int(override_val)
        else:
            if dimension.code in st.session_state.dimension_targets:
                del st.session_state.dimension_targets[dimension.code]
            st.caption("Es gilt das globale Zielniveau aus dem Sidebar.")

    st.markdown("---")

    # Fragen je Level
    for level in dimension.levels:
        if not level.questions:
            continue

        st.markdown(f"#### Reifegrad {level.level_number} – {level.name}")

        for q in level.questions:
            key = f"q_{q.id}"
            existing = st.session_state.answers.get(q.id, ANSWER_OPTIONS[0])

            try:
                idx = ANSWER_OPTIONS.index(existing)
            except ValueError:
                idx = 0

            answer = st.radio(
                q.text,
                ANSWER_OPTIONS,
                index=idx,
                key=key,
            )
            st.session_state.answers[q.id] = answer

        st.markdown("---")

    if st.button("Reifegrad neu berechnen"):
        recompute_results()
        st.success("Berechnung aktualisiert. Siehe Seiten **Dashboard** und **Priorisierung**.")


if __name__ == "__main__":
    main()
