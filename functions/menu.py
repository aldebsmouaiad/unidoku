import streamlit as st
from functions.session_state import clear_session_states, clear_session_states_except_mode_and_debug_mode, change_mode

# -Logo-
def menu_logo():
    # Verwende das vorhandene Unidoku-Logo (case-sensitive Pfad)
    logo_path = "images/unidoku.png"
    # Kein Caching hier: wir wollen Änderungen am Bild sofort sehen
    st.sidebar.image(image=logo_path)

# -Button Funktionen-
def click_back_button():
    st.session_state.warning = True

def click_cancel_button():
    del st.session_state.warning

def set_mode(mode_to_set):
    if "mode" not in st.session_state:
        st.session_state.mode = mode_to_set
        st.session_state.debug_mode = False

# -Menüs / Seitenleisten-
def debug_menu():
    if "debug_mode" in st.session_state and st.session_state.debug_mode:
        st.sidebar.markdown('#')
        st.sidebar.header("Debug")
        st.sidebar.write("Session State:")
        st.sidebar.write(st.session_state)
        st.sidebar.button(label="Session State löschen (Außer Rolle & Debug Modus)", on_click=clear_session_states_except_mode_and_debug_mode)
        st.sidebar.button(label="Session State vollständig löschen", on_click=clear_session_states)
        st.sidebar.button(label="Modus wechseln", on_click=change_mode)

def admin_check():
    """
    Funktion, die prüft ob der Nutzer als Admin eingeloggt ist. Wenn nicht, wird er zum Login weitergeleitet.
    """
    if st.session_state.mode != "analyse":
        st.warning("Sie sind nicht als Admin eingeloggt. Bitte zuerst im Admin Login anmelden.")
        st.switch_page("pages/login.py")

def default_menu():

    # Logo anzeigen
    menu_logo()

    # Importmodus Toggle
    if "import_mode" not in st.session_state:
        st.session_state.import_mode = False

    def click_import_mode_button():
        """ändert den Importmodus beim Klicken auf den Toggle"""
        st.session_state.import_mode = not st.session_state.import_mode
    
    if "mode" not in st.session_state:
        st.sidebar.warning("Modus nicht definiert!")
        st.sidebar.button(label="Modus Analyse", on_click=set_mode, kwargs={"mode_to_set": "analyse"})
        st.sidebar.button(label="Modus Fragebogen", on_click=set_mode, kwargs={"mode_to_set": "fragebogen"})
    elif st.session_state.mode == "analyse":
        # Give the toggle a stable, unique key to avoid duplicate element id errors
        st.sidebar.toggle("Importmodus", value=st.session_state.import_mode, on_change=click_import_mode_button, key="import_mode_toggle")
        if st.session_state.import_mode:
            st.sidebar.header("Navigation")
            st.sidebar.page_link("pages/analyse.py", label="Analyse")
            st.sidebar.page_link("pages/diagnose.py", label="Diagnose")
            st.sidebar.page_link("pages/login.py", label="Admin Login")
            st.sidebar.header("Import")
            st.sidebar.page_link("pages/upload.py", label="Upload")
            st.sidebar.page_link("pages/upload_beispiel.py", label="Upload Format")
        else:
            st.sidebar.header("Navigation")
            st.sidebar.page_link("pages/analyse.py", label="Analyse")
            st.sidebar.page_link("pages/diagnose.py", label="Diagnose")
            st.sidebar.page_link("pages/prognose.py", label="Prognose")
            st.sidebar.page_link("pages/user_management.py", label="Profilverwaltung")
            st.sidebar.page_link("pages/rollenverwaltung.py", label="Rollenverwaltung")
            st.sidebar.page_link("pages/admin.py", label="Administration")
            st.sidebar.page_link("pages/fragebogen_start.py", label="Fragebogen")
            st.sidebar.page_link("pages/export.py", label="Export")
            st.sidebar.page_link("pages/login.py", label="Admin Login")
            st.sidebar.header("Import")
            st.sidebar.page_link("pages/upload.py", label="Upload")
            st.sidebar.page_link("pages/upload_beispiel.py", label="Upload Format")
    elif st.session_state.mode == "fragebogen":
        st.sidebar.header("Navigation")
        st.sidebar.page_link("pages/fragebogen_start.py", label="Fragebogen")
        st.sidebar.page_link("pages/login.py", label="Admin Login")
    debug_menu()

def no_menu():

    # Logo anzeigen
    menu_logo()

    # Zurück-Button mit Warnung
    if "warning" not in st.session_state:
        st.sidebar.button(label="Zurück", use_container_width=True, on_click=click_back_button)
    else:
        st.sidebar.warning("Änderungen werden nicht gespeichert!")
        st.sidebar.button(label="Abbrechen", on_click=click_cancel_button)
        if st.sidebar.button(label="Trotzdem Zurück"):
            clear_session_states_except_mode_and_debug_mode()
            if st.session_state.mode == "analyse":
                st.switch_page("pages/kompetenzbeurteilung.py")
            elif st.session_state.mode == "fragebogen":
                st.switch_page("pages/fragebogen_start.py")
    debug_menu()
