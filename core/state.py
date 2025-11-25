# core/state.py
# Gemeinsame Initialisierung des Session-State und Sidebar-Metadaten

from datetime import date

import streamlit as st

from .scoring import LEVEL_LABELS


def ensure_session_state():
    """Legt alle benötigten Keys in st.session_state an."""
    if "meta" not in st.session_state:
        st.session_state.meta = {
            "organisation": "",
            "assessor": "",
            "date": date.today(),
            "target_label": "definiert",
            "target_level": 3,
        }
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "dimension_targets" not in st.session_state:
        st.session_state.dimension_targets = {}
    if "df_dim" not in st.session_state:
        st.session_state.df_dim = None
    if "df_cat" not in st.session_state:
        st.session_state.df_cat = None
    if "overall" not in st.session_state:
        st.session_state.overall = None
    if "priorities_df" not in st.session_state:
        st.session_state.priorities_df = None


def render_sidebar_meta():
    """Zeigt die Metadaten im Sidebar an und aktualisiert den Session-State."""
    ensure_session_state()
    meta = st.session_state.meta

    st.sidebar.subheader("Metadaten")

    org = st.sidebar.text_input("Name der Organisation", value=meta["organisation"])
    assessor = st.sidebar.text_input("Durchgeführt von", value=meta["assessor"])
    date_value = st.sidebar.date_input("Datum der Durchführung", value=meta["date"])

    target_options = [LEVEL_LABELS[i] for i in range(1, 6)] + ["Eigenes Ziel"]
    try:
        idx = target_options.index(meta["target_label"])
    except ValueError:
        idx = 2  # "definiert"

    target_label = st.sidebar.selectbox(
        "Angestrebtes Ziel (global)",
        options=target_options,
        index=idx,
    )

    if target_label != "Eigenes Ziel":
        inverse = {v: k for k, v in LEVEL_LABELS.items()}
        target_level = inverse[target_label]
    else:
        target_level = st.sidebar.slider(
            "Globales Zielniveau (1–5)",
            1,
            5,
            value=int(meta["target_level"]),
        )

    meta.update(
        organisation=org,
        assessor=assessor,
        date=date_value,
        target_label=target_label,
        target_level=int(target_level),
    )
    st.session_state.meta = meta
    return meta
