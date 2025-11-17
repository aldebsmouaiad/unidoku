import streamlit as st
import pandas as pd
from functions.menu import default_menu
from functions.page import footer
from functions.user_management import create_profile
from functions.initialize import initialize_fragebogen_einleitung
from config import GOOGLE_SHEET_PROFILES, COLUMN_PROFILE_ID
from functions.database import get_dataframe_from_gsheet
from functions.session_state import check_mode

# -Seitenkonfiguration-
st.set_page_config(page_title="Fragebogen", layout="wide")
check_mode()
default_menu()

# -Seiteninhalt-
st.title("Fragebogen")

begin_fragebogen = st.button(label="Fragebogen starten")
if begin_fragebogen:
    initialize_fragebogen_einleitung()
    st.switch_page("pages/fragebogen_einleitung.py")

# Fußzeile
footer()
