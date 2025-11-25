# pages/03_Priorisierung.py
# Gaps priorisieren und Maßnahmen planen

import streamlit as st

from core.model_loader import load_model
from core.state import ensure_session_state, render_sidebar_meta
from core.scoring import compute_results


def ensure_results():
    model = load_model()
    meta = st.session_state.meta
    if st.session_state.df_dim is None:
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
    ensure_results()

    df_dim = st.session_state.df_dim

    st.title("Priorisierung – Handlungsfelder planen")

    if df_dim is None or df_dim.empty:
        st.info("Noch keine Ergebnisse vorhanden. Bitte zuerst die Erhebung ausfüllen.")
        return

    st.markdown(
        """
Hier kannst du die Dimensionen mit den größten Gaps priorisieren und Maßnahmen planen.  
Die Spalten **Priorität**, **Maßnahme** und **Zeitraum** sind editierbar.
"""
    )

    df_dim = df_dim.sort_values("Gap", ascending=False)
    df_dim["Dimension"] = df_dim["Code"] + " – " + df_dim["Name"]

    # Bisherige Priorisierungen übernehmen
    if st.session_state.priorities_df is not None:
        prev = st.session_state.priorities_df[["Code", "Priorität", "Maßnahme", "Zeitraum"]]
        df_dim = df_dim.merge(prev, on="Code", how="left")
    else:
        df_dim["Priorität"] = ""
        df_dim["Maßnahme"] = ""
        df_dim["Zeitraum"] = ""

    edit_cols = ["Code", "Dimension", "Ist", "Soll", "Gap", "Priorität", "Maßnahme", "Zeitraum"]

    edited = st.data_editor(
        df_dim[edit_cols],
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ist": st.column_config.NumberColumn(format="%.2f"),
            "Soll": st.column_config.NumberColumn(format="%.0f"),
            "Gap": st.column_config.NumberColumn(format="+.2f"),
        },
        key="prio_editor",
    )

    st.session_state.priorities_df = edited

    st.caption(
        "Die hier gesetzten Prioritäten und Maßnahmen werden beim CSV/PDF-Export mit ausgegeben."
    )


if __name__ == "__main__":
    main()
