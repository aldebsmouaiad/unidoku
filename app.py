# app.py
# Startseite der Streamlit-Multipage-App

from datetime import date

import streamlit as st

from core.model_loader import load_model
from core.state import ensure_session_state, render_sidebar_meta

st.set_page_config(
    page_title="Reifegradmodell Technische Dokumentation",
    layout="wide",
)

# Session-State initialisieren und Sidebar-Metadaten anzeigen
ensure_session_state()
meta = render_sidebar_meta()

model = load_model()

st.title("Reifegradmodell – Technische Dokumentation & Organisation")

st.markdown(
    f"""
**Modell:** {model.name}

Diese Anwendung bildet ein Reifegrad-Erhebungstool nach, das ursprünglich als Excel-Tool
entwickelt wurde.

**So nutzt du die App:**

1. Lege im linken Sidebar Organisation, Datum und globales Zielniveau fest.
2. Gehe zur Seite **„Erhebung“** (oben links im Seiten-Menü) und beantworte die Fragen.
3. Schaue dir unter **„Dashboard“** die Radarplots und Tabellen an und exportiere CSV / PDF.
4. Priorisiere unter **„Priorisierung“** die größten Gaps und plane Maßnahmen.
5. Nutze das **„Glossar“**, um Begriffe nachzuschlagen.

Alle Eingaben werden nur für die aktuelle Sitzung im Speicher gehalten und
nicht dauerhaft gespeichert.
"""
)
