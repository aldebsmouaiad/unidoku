import streamlit as st

st.session_state.mode = "fragebogen"
st.session_state.debug_mode = True

# -Startseite öffnen-
st.switch_page("pages/fragebogen_start.py")
