import streamlit as st
import pandas as pd
import time
import datetime as dt
import pytz

from pages.user_management import submenu_roles

from functions.menu import default_menu, admin_check
from functions.page import footer
from config import GOOGLE_SHEET_PROFILES, COLUMN_PROFILE_ID, GOOGLE_SHEET_BEDARFE, GOOGLE_SHEET_ANSWERS, COLUMN_INDEX, COLUMN_ROLE, CLUSTER_COLUMNS, PATH_QUESTIONNAIRE
from functions.database import get_dataframe_from_gsheet, update_dataframe_to_gsheet
from functions.session_state import clear_session_states_except_mode_and_debug_mode, check_mode

# -Seitenkonfiguration-
st.set_page_config(page_title="Rollenverwaltung", layout="wide")
check_mode()
admin_check()
default_menu()


# -Daten einlesen-
data_bedarfe = get_dataframe_from_gsheet(GOOGLE_SHEET_BEDARFE, index_col=COLUMN_INDEX)
data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)
answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)
fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=';', encoding='utf-8')
unique_cluster_names = fragebogen["Cluster-Name"].unique().tolist()


# -Unterseiten-
def submenu_data():
    if st.button("Daten aktualisieren", key="update_data_button"):
        st.cache_data.clear()
        st.rerun(scope="app")
    st.subheader("Datenpunkte Rollen")
    st.write(data_bedarfe)

    st.subheader("Aktuelle Rollenzuweisung")
    st.write(data_profiles.sort_index())

def submenu_new():
    role_selection = st.pills(label="Wie möchten Sie die Rolle auswählen?", options=["Bestehende Rolle übernehmen", "Neue Rolle erstellen"], default=None)
    unique_roles = data_bedarfe[COLUMN_ROLE].unique().tolist()
    if role_selection == "Bestehende Rolle übernehmen":
        set_role = st.selectbox(label="Rolle auswählen:", options=unique_roles, index=None, placeholder="Rolle")
        if  set_role:
            id_role = data_bedarfe.loc[data_bedarfe[COLUMN_ROLE] == set_role, "Rollen-ID"].values[0]
    elif role_selection == "Neue Rolle erstellen":
        set_role = st.text_input("Rollen-Name:")
        if set_role in unique_roles:
            st.warning(f"Es ist bereits eine Rolle mit dem Namen {set_role} vorhanden.")
        id_role = data_bedarfe["Rollen-ID"].values[-1] + 1
    else:
        set_role = None

    st.markdown("")
    date_selection = st.pills(label="Für welchen Zeitpunkt soll der Datenpunkt angelegt werden?", options=["Jetzt", "Datum eingeben"], default=None)
    if date_selection == "Jetzt":
        timezone = pytz.timezone('Europe/Berlin')
        set_date = dt.datetime.now(timezone)
    elif date_selection == "Datum eingeben":
        set_date = st.date_input("Datum eingeben:", format="DD.MM.YYYY", value=None)
    else:
        set_date = None

    if not set_role or not set_date:
        st.stop()

    st.markdown("")
    with st.form("values_bedarfe", border=True):
        st.subheader("Bedarfswerte der Rollen", help="Werte zwischen 1 und 5; 1 entspricht niedriger Anforderung, 5 entspricht hoher Anforderung")
        for cluster_name in unique_cluster_names:
            if f"value_{cluster_name}" not in st.session_state:
                st.session_state[f"value_{cluster_name}"] = None
            st.number_input(label=cluster_name, min_value=1.0, max_value=5.0, step=0.1, key=f"value_{cluster_name}")
        submit_button = st.form_submit_button("Datenpunkt anlegen")
    if submit_button:
        cluster_values = []
        for cluster_name in unique_cluster_names:
            if not st.session_state[f"value_{cluster_name}"]:
                st.warning("Bitte geben Sie für alle Cluster einen Wert an")
                st.stop()
            # Rundung auf 1 Nachkommastelle
            cluster_values.append(round(st.session_state[f"value_{cluster_name}"], 1))
        formatted_date = set_date.strftime('%d.%m.%Y %H:%M')
        data = {
            "Speicherzeitpunkt": formatted_date,
            "Rollen-ID": id_role,
            "Rollen-Name": set_role,
            **{key: value for key, value in zip(CLUSTER_COLUMNS, cluster_values)}
        }
        new_row = pd.DataFrame(data, index=[0])
        updated_bedarfe = pd.concat([data_bedarfe, new_row], ignore_index=True)
        update_dataframe_to_gsheet(GOOGLE_SHEET_BEDARFE, updated_bedarfe)
        st.rerun(scope="app")


def submenu_edit():
    if len(data_bedarfe) > 0:
        st.subheader("Datenpunkte Rollen")
        edited_df = st.data_editor(
            data = data_bedarfe,
            hide_index= True,
            column_order= ["Rollen-ID", "Speicherzeitpunkt", "Rollen-Name"] + CLUSTER_COLUMNS,
            disabled= ["Rollen-ID", "Speicherzeitpunkt", "Rollen-Name"],
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
        if st.button(label="Änderungen speichern", key="save_changes_button"):
            updated_answers = answers.copy()
            updated_answers.update(edited_df)
            update_dataframe_to_gsheet("antworten_test", updated_answers)
            st.rerun(scope="app")
    else:
        st.warning("Keine Datenpunkte gefunden gefunden.")


# -Seiteninhalt-
st.title("Rollenverwaltung")

submenu_options = ["Daten", "Neuer Datenpunkt", "Datenpunkte bearbeiten", "Rollen zuweisen"]

submenu_functions = {
    "Daten": submenu_data,
    "Neuer Datenpunkt": submenu_new,
    "Datenpunkte bearbeiten": submenu_edit,
    "Rollen zuweisen": submenu_roles
}

selected_submenu = st.segmented_control(label="submenu", options=submenu_options, default=submenu_options[0], label_visibility="collapsed", on_change=clear_session_states_except_mode_and_debug_mode)

submenu_functions[selected_submenu]()

# Fußzeile
footer()
