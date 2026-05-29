# core/model_loader.py
from __future__ import annotations

from pathlib import Path
import json
import streamlit as st

from core.i18n import get_language, normalize_language

# Basisverzeichnis: .../unidoku/
BASE_DIR = Path(__file__).resolve().parent.parent


@st.cache_data
def _load_model_config_for_language(language: str) -> dict:
    """
    Lädt die Reifegradmodell-Konfiguration aus data/models.
    """
    filename = "niro_td_model_en.json" if normalize_language(language) == "en" else "niro_td_model.json"
    path = BASE_DIR / "data" / "models" / filename
    if not path.exists():
        raise FileNotFoundError(f"Modelldatei nicht gefunden: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_model_config(language: str | None = None) -> dict:
    return _load_model_config_for_language(normalize_language(language or get_language()))


@st.cache_data
def _load_tool_meta_for_language(language: str) -> dict:
    """
    Lädt Metadaten für Start/Intro aus data/niro_td_meta*.json.
    (separate Datei, unabhängig vom Modell)
    """
    filename = "niro_td_meta_en.json" if normalize_language(language) == "en" else "niro_td_meta.json"
    path = BASE_DIR / "data" / filename
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data if isinstance(data, dict) else {}


def load_tool_meta(language: str | None = None) -> dict:
    return _load_tool_meta_for_language(normalize_language(language or get_language()))


@st.cache_data
def load_glossary():
    path = BASE_DIR / "data" / "glossary.json"
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

    if isinstance(data, dict):
        return data

    return {}
