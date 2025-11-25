# app.py
import streamlit as st
from pathlib import Path
import importlib.util

from core.state import init_session_state

# -------------------------------------------------------
# Globale Streamlit-Konfiguration
# -------------------------------------------------------
st.set_page_config(
    page_title="Reifegradmodell Technische Dokumentation",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent


# -------------------------------------------------------
# Hilfsfunktion: Page-Module aus pages/-Ordner laden
# (auch wenn sie "01_Erhebung.py" usw. heißen)
# -------------------------------------------------------
def load_page_module(filename: str, module_name: str):
    """
    Lädt eine Python-Datei aus dem Unterordner 'pages' als Modul
    und gibt das Modulobjekt zurück.
    """
    file_path = BASE_DIR / "pages" / filename
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# Page-Module einmalig laden
page_erhebung = load_page_module("01_Erhebung.py", "page_erhebung")
page_dashboard = load_page_module("02_Dashboard.py", "page_dashboard")
page_priorisierung = load_page_module("03_Priorisierung.py", "page_priorisierung")
page_glossar = load_page_module("04_Glossar.py", "page_glossar")


# -------------------------------------------------------
# Start-Seite
# -------------------------------------------------------
def render_start():
    st.title("Reifegradmodell Technische Dokumentation")

    st.markdown(
        """
Willkommen im **Reifegrad-Tool**.

Über die Navigation in der **linken Sidebar** kannst du zwischen:

- **Start**
- **Erhebung**
- **Dashboard**
- **Priorisierung**
- **Glossar**

wechseln.

Die App speichert keine Daten dauerhaft. Ergebnisse können später als CSV/PDF exportiert werden.
"""
    )


# -------------------------------------------------------
# Hauptfunktion
# -------------------------------------------------------
def main():
    # Session-State immer initialisieren (einmal pro Run)
    init_session_state()

    # Sidebar-Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Seite wählen",
        ["Start", "Erhebung", "Dashboard", "Priorisierung", "Glossar"],
    )

    if page == "Start":
        render_start()
    elif page == "Erhebung":
        page_erhebung.main()
    elif page == "Dashboard":
        page_dashboard.main()
    elif page == "Priorisierung":
        page_priorisierung.main()
    elif page == "Glossar":
        page_glossar.main()


if __name__ == "__main__":
    main()
