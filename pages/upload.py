import streamlit as st
import pandas as pd
from functions.menu import default_menu, admin_check
from functions.page import footer
from functions.session_state import check_mode
from config import GOOGLE_SHEET_ANSWERS, GOOGLE_SHEET_PROFILES, GOOGLE_SHEET_BEDARFE

# -Seitenkonfiguration-
st.set_page_config(page_title="Upload", layout="wide")
check_mode()
admin_check()
default_menu()

# -Seiteninhalt-
st.title("Upload")

if "uploaded_data" not in st.session_state:
    st.session_state["uploaded_data"] = {}

# -Info-
st.info(
    "Hier können Sie eigene Daten in das System uploaden. \n\n"
    "Bitte zwingend an das Format der Beispiel Dateien halten (aus -Upload Format-)!\n\n"
    "Die Dateien müssen im CSV-Format (UTF-8) mit einem Semikolon (;) als Trennzeichen und einem Komma (,) als Dezimaltrennzeichen vorliegen.\n\n"
)

# -Upload Buttons-
fragebogen_file = st.file_uploader("Upload Fragebogen", type="csv", key="upload_fragebogen")
answers_file = st.file_uploader("Upload Antworten (Ausgefüllte Fragebögen)", type="csv", key="upload_answers")
profiles_file = st.file_uploader("Upload Profile", type="csv", key="upload_profiles")
roles_file = st.file_uploader("Upload Rollen-Bedarfe", type="csv", key="upload_roles")


def read_csv_semicolon(file):
    try:
        return pd.read_csv(file, sep=";", decimal=",", encoding="utf-8")
    except Exception:
        file.seek(0)
        return pd.read_csv(file, sep=";", decimal=",", encoding="unicode_escape")

colA, colB = st.columns(2)
with colA:
    if fragebogen_file is not None:
        df_fragebogen = read_csv_semicolon(fragebogen_file)
        st.session_state["uploaded_data"]["fragebogen"] = df_fragebogen
        st.success("Fragebogen geladen und bereitgestellt.")
    if answers_file is not None:
        df_answers = read_csv_semicolon(answers_file)
        st.session_state["uploaded_data"][GOOGLE_SHEET_ANSWERS] = df_answers
        st.success("Ausgefüllte Fragebögen geladen und bereitgestellt.")
with colB:
    if profiles_file is not None:
        df_profiles = read_csv_semicolon(profiles_file)
        st.session_state["uploaded_data"][GOOGLE_SHEET_PROFILES] = df_profiles
        st.success("Profile geladen und bereitgestellt.")
    if roles_file is not None:
        df_roles = read_csv_semicolon(roles_file)
        st.session_state["uploaded_data"][GOOGLE_SHEET_BEDARFE] = df_roles
        st.success("Rollen-Bedarfe geladen und bereitgestellt.")


if any([profiles_file, answers_file, roles_file, fragebogen_file]):
    with st.expander("Vorschau der geladenen Daten"):
        if fragebogen_file is not None:
            st.subheader("Fragebogen")
            st.dataframe(st.session_state["uploaded_data"]["fragebogen"].head(10))
        if answers_file is not None:
            st.subheader("Antworten")
            st.dataframe(st.session_state["uploaded_data"][GOOGLE_SHEET_ANSWERS].head(10))
        if profiles_file is not None:
            st.subheader("Profile")
            st.dataframe(st.session_state["uploaded_data"][GOOGLE_SHEET_PROFILES].head(10))
        if roles_file is not None:
            st.subheader("Rolen-Bedarfe")
            st.dataframe(st.session_state["uploaded_data"][GOOGLE_SHEET_BEDARFE].head(10))

# Fußzeile
footer()