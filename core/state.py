# core/state.py
import streamlit as st


def init_session_state():
    """
    Standardwerte einmalig in st.session_state setzen.

    WICHTIG:
    - meta enthält definierte Keys, damit Dashboard/Export stabil und "identisch" bleiben.
    """
    defaults = {
        "answers": {},               # Antworten pro Frage-ID
        "global_target_level": 3.0,  # globales Soll-Niveau
        "dimension_targets": {},     # optionale Soll-Overrides je Dimension
        "priorities": {},            # Maßnahmen / Kommentare je Dimension
        "nav_page": "Start",
        "erhebung_step": 0,          # 0 = Eingabemaske, 1 = Eigenes Ziel (Tabelle), 2 = Fragen
        "erhebung_dim_idx": 0,       # aktuelle Dimension (Index)
        "erhebung_dim_idx_ui": 0,    # UI-Key für Selectbox im Footer
        "erhebung_own_target_defined": False,

        # Metadaten der Erhebung (Excel-Dashboard)
        "meta": {
            "org": "",
            "area": "",              # neu: Bereich
            "assessor": "",
            "assessor_contact": "",
            "date_str": "",
            "target_label": "",
        },
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Falls meta bereits existiert (z.B. aus älteren Sessions), fehlende Keys ergänzen
    if "meta" in st.session_state and isinstance(st.session_state["meta"], dict):
        for mk, mv in defaults["meta"].items():
            st.session_state["meta"].setdefault(mk, mv)
