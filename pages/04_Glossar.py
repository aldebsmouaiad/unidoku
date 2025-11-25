# pages/04_Glossar.py
# Glossar-Ansicht

import streamlit as st

from core.model_loader import load_glossary
from core.state import ensure_session_state, render_sidebar_meta


def main():
    ensure_session_state()
    render_sidebar_meta()  # nur zur Konsistenz
    glossary = load_glossary()

    st.title("Glossar")

    if not glossary:
        st.info("Noch kein Glossar hinterlegt.")
        return

    query = st.text_input("Begriff oder Stichwort suchen", "")

    if query:
        q = query.lower()
        filtered = [
            g
            for g in glossary
            if q in g.get("term", "").lower() or q in g.get("definition", "").lower()
        ]
    else:
        filtered = glossary

    for entry in filtered:
        with st.expander(entry.get("term", "")):
            st.write(entry.get("definition", ""))


if __name__ == "__main__":
    main()
