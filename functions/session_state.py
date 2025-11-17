import streamlit as st

def clear_session_states():
    for key in st.session_state.keys():
        del st.session_state[key]

def clear_session_states_except_mode_and_debug_mode():
    for key in st.session_state.keys():
        if key != "mode" and key != "debug_mode":
            del st.session_state[key]

def change_mode():
    if "mode" in st.session_state:
        st.session_state.mode = "fragebogen" if st.session_state.mode == "analyse" else "analyse"

def check_mode():
    if "mode" not in st.session_state:
        st.session_state.mode = "fragebogen"
        st.session_state.debug_mode = False

def require_uploaded_data(required_keys):
    """Prüft, ob im Importmodus alle benötigten Upload-Daten vorhanden sind.

    - required_keys: Iterable von Schlüsseln, die innerhalb von st.session_state["uploaded_data"] vorhanden sein müssen.
    - Bei fehlenden Daten wird eine Warnung angezeigt und die Ausführung mit st.stop() beendet.
    """
    # Sicherstellen, dass der Container existiert
    if "uploaded_data" not in st.session_state:
        missing = list(required_keys)
    else:
        missing = [k for k in required_keys if k not in st.session_state["uploaded_data"]]

    if missing:
        st.warning(
            "Es fehlen folgende hochgeladene Dateien/Daten im Importmodus: "
            + ", ".join(str(m) for m in missing)
            + ". Bitte laden Sie diese unter 'Upload' hoch."
        )
        st.stop()
    return True