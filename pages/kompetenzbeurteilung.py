import streamlit as st
import pandas as pd
from functions.menu import default_menu
from functions.page import footer
from config import GOOGLE_SHEET_PROFILES, COLUMN_PROFILE_ID, GOOGLE_SHEET_ANSWERS, COLUMN_INDEX
from functions.database import get_dataframe_from_gsheet
from functions.session_state import check_mode

# -Seitenkonfiguration-
st.set_page_config(page_title="Kompetenzbeurteilung", layout="wide")
check_mode()
default_menu()

# -Tabelle für Profil verknüpfen-
data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)

# -Tabelle für Antworten verknüpfen-
answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)

# -Titel-
st.title("Kompetenzbeurteilung")

# -Profilauswahl-
selected_id_active_profile = st.selectbox(label="Welcher MA soll beurteilt werden?", options=data_profiles.index, index=None, placeholder="Bitte Profil auswählen")

if selected_id_active_profile is not None:
    selected_name_active_profile = data_profiles.loc[selected_id_active_profile, "Name"]
    amount_answered_forms = len(answers.loc[answers["Profil-ID"] == selected_id_active_profile])
    st.write(f"Ausgewähltes Profil: {selected_name_active_profile}")
    if amount_answered_forms == 1:
        st.write(f"Für das Profil wurde bereits ein Fragebogen ausgefüllt.")
    elif amount_answered_forms > 1:
        st.write(f"Für das Profil wurden bereits {amount_answered_forms} Fragebögen ausgefüllt.")
    else:
        st.write("Für das Profil wurde noch kein Fragebogen ausgefüllt.")

    st.markdown('#')

    st.write("Wie möchten Sie Daten aufnehmen?")

    left, right = st.columns(2)
    with left:
        if st.button(label="Fragebogen ausfüllen"):
            st.session_state.id_active_profile = selected_id_active_profile
            st.session_state.name_active_profile = selected_name_active_profile
            st.switch_page("pages/fragebogen.py")
    with right:
        if st.button(label="Kompetenzen manuell festlegen"):
            st.session_state.id_active_profile = selected_id_active_profile
            st.session_state.name_active_profile = selected_name_active_profile
            st.switch_page("pages/kompetenzen_festlegen.py")

# Fußzeile
footer()
