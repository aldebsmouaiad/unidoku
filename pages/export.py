import streamlit as st
import pandas as pd
from functions.menu import default_menu, admin_check
from functions.page import footer
from functions.database import get_dataframe_from_gsheet
from functions.session_state import check_mode
from config import GOOGLE_SHEET_ANSWERS, COLUMN_INDEX, GOOGLE_SHEET_PROFILES, GOOGLE_SHEET_BEDARFE, COLUMN_PROFILE_ID, PATH_QUESTIONNAIRE

# -Seitenkonfiguration-
st.set_page_config(page_title="Export", layout="wide")
check_mode()
admin_check()
default_menu()


# Funktion zum Umwandeln in csv
def convert_for_download(df):
    return df.to_csv(sep=';', decimal=",", encoding="utf-8")

# Tabelle für Antworten verknüpfen und in csv umwandeln
data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)
data_profiles_csv = convert_for_download(data_profiles)
data_answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)
data_answers_csv = convert_for_download(data_answers)
data_bedarfe = get_dataframe_from_gsheet(GOOGLE_SHEET_BEDARFE, index_col=COLUMN_INDEX)
data_bedarfe_csv = convert_for_download(data_bedarfe)
data_fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=';')
data_fragebogen_csv = data_fragebogen.to_csv(sep=';', index=False)


# -Seiteninhalt-
st.title("Export")
st.info(
    "Hier können Sie die Daten aus dem System exportieren. Die Daten werden im CSV-Format bereitgestellt und können z.B. in Excel geöffnet werden.\n\n"
    "Die Daten werden mit einem Semikolon (;) als Trennzeichen und einem Komma (,) als Dezimaltrennzeichen exportiert.\n\n"
    "Die Kodierung der Dateien ist UTF-8."
)

# -Download Buttons-
st.download_button(label="Export Fragebogen", data=data_fragebogen_csv, file_name="Fragebogen.csv")
st.download_button(label="Export Profile", data=data_profiles_csv, file_name="profile.csv")
st.download_button(label="Export ausgefüllte Fragebögen", data=data_answers_csv, file_name="antworten.csv")
st.download_button(label="Export Rollen", data=data_bedarfe_csv, file_name="rollen.csv")


# Fußzeile
footer()
