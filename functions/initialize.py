import streamlit as st
from functions import data

def initialize_fragebogen_einleitung():
    # Funktion zum Initialisieren der Session States für die Fragebogen Einleitung.
    if "einleitung_page" not in st.session_state:
        st.session_state.einleitung_page = 1

    # current_answers initialisieren
    if "current_answers" not in st.session_state:
        st.session_state.current_answers = {}

    # Profil-ID initialisieren
    if "id_active_profile" not in st.session_state:
        st.session_state.id_active_profile = None

def initialize_fragebogen():
    # einleitung_page aus dem Session State löschen
    if "einleitung_page" in st.session_state:
        del st.session_state.einleitung_page

    # Funktion zum Initialisieren der Session States für den Fragebogen.
    if "page" not in st.session_state:
        st.session_state.page = 1

    # Nur Fragebogen-Antworten initialisieren, demographische Antworten beibehalten
    question_ids = data.get_question_ids()
    for frage_id in question_ids:
        if frage_id not in st.session_state.current_answers:
            st.session_state.current_answers[frage_id] = None
