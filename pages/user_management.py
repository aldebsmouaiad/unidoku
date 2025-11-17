import streamlit as st
import pandas as pd
import time
from functions.menu import default_menu, admin_check
from functions.page import footer
from functions.user_management import create_profile
from config import GOOGLE_SHEET_PROFILES, COLUMN_PROFILE_ID, GOOGLE_SHEET_ANSWERS, GOOGLE_SHEET_BEDARFE, COLUMN_INDEX
from functions.database import get_dataframe_from_gsheet, update_dataframe_to_gsheet
from functions.session_state import clear_session_states_except_mode_and_debug_mode, check_mode

# -Seitenkonfiguration-
st.set_page_config(page_title="Profilverwaltung", layout="wide")
check_mode()
admin_check()
default_menu()


# -Daten einlesen-
data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)
data_bedarfe = get_dataframe_from_gsheet(GOOGLE_SHEET_BEDARFE, index_col=COLUMN_INDEX)
answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)

# -Unterseiten-
def submenu_data():
    if st.button("Daten aktualisieren", key="update_data_button_from_user_management"):
        st.cache_data.clear()
        st.rerun(scope="app")
    st.subheader("Vorhandene Profile")
    st.write(data_profiles.sort_index())

    st.subheader("Ausgefüllte Fragebögen")
    st.write(answers)

def submenu_add():
    set_id_active_profile = st.number_input(label="Profil-ID (zwischen 101 und 999):", min_value=101, max_value=999, value=None)
    st.button(label="ID prüfen", key="check_id_button_from_user_management")
    if set_id_active_profile in data_profiles.index:
        st.warning(f"Ein Profil mit der ID {set_id_active_profile} ist bereits vorhanden.")
    elif set_id_active_profile:
        set_name_active_profile = st.text_input(label="Profil Name")
        options_roles = data_bedarfe["Rollen-Name"].unique()
        set_role_active_profile = st.selectbox(label="Rolle", options=options_roles, index=None, placeholder="Rolle auswählen")
        if st.button("Profil anlegen", key="create_profile_button_from_user_management"):
            create_profile(id=set_id_active_profile, name=set_name_active_profile, role=set_role_active_profile)
            st.rerun(scope="app")

def submenu_edit_profiles():
    if len(data_profiles) > 0:
        st.subheader("Profile")
        edited_df = st.data_editor(
            data = data_profiles,
            hide_index= False,
            column_order= ["Profil-ID", "Name", "Rollen-Name"],
            disabled= ["Profil-ID"],
            column_config = {
                "Name": st.column_config.TextColumn(
                    label="Name",
                    help="Hier können Sie den Namen für das Profil festlegen.",
                    max_chars=50
                ),
                "Rollen-Name": st.column_config.TextColumn(
                    label="Aktuelle Rolle",
                    help="Hier können Sie die aktuelle Rolle für das Profil festlegen.",
                    max_chars=50
                )
            }
        )
        if st.button(label="Änderungen speichern", key="save_changes_button_from_user_management"):
            updated_answers = answers.copy()
            updated_answers.update(edited_df)
            update_dataframe_to_gsheet("antworten_test", updated_answers)
            st.rerun(scope="app")
    else:
        st.warning("Keine Profile gefunden.")


def submenu_roles():
    set_id_active_profile = None
    toggle_filter = st.toggle("Nach Profil filtern")
    if toggle_filter:
        options_profiles = data_profiles["Name"].unique().tolist()
        set_name_active_profile = st.selectbox(label="Profil auswählen:", options=options_profiles)
        if set_name_active_profile:
            set_id_active_profile = data_profiles.loc[data_profiles["Name"] == set_name_active_profile].index[0]
            st.write(f"Profil-ID: {int(set_id_active_profile)}")
    if toggle_filter:
        filtered_answers = answers[answers["Profil-ID"] == set_id_active_profile]
    else:
        filtered_answers = answers.copy()
    if len(filtered_answers) > 0:
        st.subheader("Datenpunkte")
        edited_df = st.data_editor(
            data = filtered_answers,
            hide_index= True,
            column_order= ["Profil-ID", "Speicherzeitpunkt", "Rollen-Name"],
            disabled = ["Profil-ID", "Speicherzeitpunkt"],
            column_config = {
                "Rollen-Name": st.column_config.TextColumn(
                    label="Rollen-Name",
                    help="Hier können Sie die Rolle für das Profil festlegen.",
                    max_chars=50
                )
            }
        )
        if st.button(label="Änderungen speichern", key="save_changes_button_2_from_user_management"):
            updated_answers = answers.copy()
            updated_answers.update(edited_df)
            update_dataframe_to_gsheet("antworten_test", updated_answers)
            st.rerun(scope="app")
    else:
        st.warning("Keine Antworten für dieses Profil gefunden.")


# -Seiteninhalt-
st.title("Profilverwaltung")

submenu_options = ["Daten", "Profil hinzufügen", "Profil bearbeiten", "Rollen zuweisen"]

submenu_functions = {
    "Daten": submenu_data,
    "Profil hinzufügen": submenu_add,
    "Profil bearbeiten": submenu_edit_profiles,
    "Rollen zuweisen": submenu_roles
}

selected_submenu = st.segmented_control(label="submenu", options=submenu_options, default=submenu_options[0], label_visibility="collapsed", on_change=clear_session_states_except_mode_and_debug_mode)

submenu_functions[selected_submenu]()

# Fußzeile
footer()
