# core/model_loader.py
from __future__ import annotations

from pathlib import Path
import json
import streamlit as st

# Basisverzeichnis: .../unidoku/
BASE_DIR = Path(__file__).resolve().parent.parent


@st.cache_data
def load_model_config() -> dict:
    """
    Lädt die Reifegradmodell-Konfiguration aus data/models/niro_td_model.json.
    """
    path = BASE_DIR / "data" / "models" / "niro_td_model.json"
    if not path.exists():
        raise FileNotFoundError(f"Modelldatei nicht gefunden: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data

def load_glossary():
    path = Path("data/glossary.json")
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Falls Liste von Einträgen: in Dict umwandeln
    if isinstance(data, list):
        return {
            (item.get("term") or item.get("name") or item.get("Begriff") or ""):
            (item.get("definition") or item.get("text") or item.get("Beschreibung") or "")
            for item in data
            if (item.get("term") or item.get("name") or item.get("Begriff"))
        }

    # Falls schon Dict: einfach zurückgeben
    if isinstance(data, dict):
        return data

    # Fallback
    return {}