# pages/04_Glossar.py
import streamlit as st

from core.state import init_session_state
from core.model_loader import load_glossary


def main():
    # Session-State initialisieren (falls wir später noch mehr dort ablegen)
    init_session_state()

    st.title("Glossar")

    glossary = load_glossary()
    if not glossary:
        st.info("Noch kein Glossar hinterlegt (data/glossary.json).")
        return

    # Suchfeld
    query = st.text_input("Begriff suchen", "")

    # Begriffe alphabetisch durchsuchen und anzeigen
    for term, definition in sorted(glossary.items()):
        if query and query.lower() not in term.lower():
            continue

        st.markdown(f"**{term}**")
        st.write(definition)
        st.markdown("---")


if __name__ == "__main__":
    main()
