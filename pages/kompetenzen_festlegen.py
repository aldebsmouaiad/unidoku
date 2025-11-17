import streamlit as st
import pandas as pd
from functions.menu import no_menu
from functions.page import footer
from functions.session_state import check_mode

# -Seitenkonfiguration-
st.set_page_config(page_title="Kompetenzen festlegen", layout="wide")
check_mode()
no_menu()

# -Seiteninhalt-
st.title("Kompetenzen festlegen")
st.write("Keine Funktionalität implementiert.")
st.write("")
st.write("Ideen:")
level_kompetenzen= (1, 2, 4, 5, 5)

antworten = st.select_slider(label="Kompetenz 1", options=level_kompetenzen)
st.radio(label="Kompetenz 2", options=level_kompetenzen, index=None, horizontal=True)

# Fußzeile
footer()
