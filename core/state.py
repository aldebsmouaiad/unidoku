# core/state.py
import streamlit as st

def init_session_state():
    """
    Standardwerte einmalig in st.session_state setzen.
    """
    defaults = {
        "answers": {},              # Antworten pro Frage-ID
        "global_target_level": 3.0, # globales Soll-Niveau
        "dimension_targets": {},    # optionale Soll-Overrides je Dimension
        "priorities": {},           # Maßnahmen / Kommentare je Dimension
        "meta": {},                 # Metadaten zur Erhebung (Organisation etc.)
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
