import streamlit as st

st.set_page_config(page_title="Sidebar-Test", layout="wide")

st.title("Sidebar-Test")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Seite wählen", ["A", "B", "C"])

st.write(f"Ausgewählte Seite: {page}")
