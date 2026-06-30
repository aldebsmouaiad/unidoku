# core/model_loader.py
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from core.i18n import get_language, normalize_language


# Basisverzeichnis: .../unidoku/
BASE_DIR = Path(__file__).resolve().parent.parent


def _json_cache_token(path: Path) -> str:
    try:
        stat = path.stat()
        return f"{stat.st_mtime_ns}:{stat.st_size}"
    except OSError:
        return "missing"


@st.cache_data
def _load_json_file(path_str: str, cache_token: str) -> dict:
    """Load JSON with a file-token argument so Streamlit Cloud cache refreshes."""
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"JSON-Datei nicht gefunden: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data if isinstance(data, dict) else {}


def _load_json_file_uncached(path: Path) -> dict:
    return _load_json_file(str(path), _json_cache_token(path))


def _model_path_for_language(language: str) -> Path:
    filename = "niro_td_model_en.json" if normalize_language(language) == "en" else "niro_td_model.json"
    return BASE_DIR / "data" / "models" / filename


def load_model_config(language: str | None = None) -> dict:
    """
    Laedt die Reifegradmodell-Konfiguration aus data/models.
    Der Dateitoken verhindert stale Streamlit-Cloud-Caches nach Deployments.
    """
    return _load_json_file_uncached(_model_path_for_language(normalize_language(language or get_language())))


def _meta_path_for_language(language: str) -> Path:
    filename = "niro_td_meta_en.json" if normalize_language(language) == "en" else "niro_td_meta.json"
    return BASE_DIR / "data" / filename


def load_tool_meta(language: str | None = None) -> dict:
    """
    Laedt Metadaten fuer Start/Intro aus data/niro_td_meta*.json.
    (separate Datei, unabhaengig vom Modell)
    """
    path = _meta_path_for_language(normalize_language(language or get_language()))
    if not path.exists():
        return {}
    return _load_json_file_uncached(path)


@st.cache_data
def load_glossary():
    path = BASE_DIR / "data" / "glossary.json"
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Falls Liste von Eintraegen: in Dict umwandeln
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
