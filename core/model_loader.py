# core/model_loader.py
# Laden der JSON-Konfiguration und des Glossars

from pathlib import Path
from typing import List
import json

import streamlit as st

from .types import Question, Level, Dimension, MaturityModel

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "data" / "models" / "niro_td_model.json"
GLOSSARY_PATH = BASE_DIR / "data" / "glossary.json"


def _parse_model(raw: dict) -> MaturityModel:
    levels_info = {int(k): v for k, v in raw.get("levels_info", {}).items()}

    dimensions: List[Dimension] = []
    for d in raw.get("dimensions", []):
        levels: List[Level] = []
        for l in d.get("levels", []):
            questions = [
                Question(
                    id=q["id"],
                    text=q["text"],
                    help_text=q.get("help_text"),
                )
                for q in l.get("questions", [])
            ]
            levels.append(
                Level(
                    level_number=int(l["level_number"]),
                    name=l.get("name", f"Stufe {l['level_number']}"),
                    questions=questions,
                )
            )

        dimensions.append(
            Dimension(
                code=d["code"],
                name=d["name"],
                category=d.get("category", "TD"),
                description=d.get("description"),
                default_target_level=int(d.get("default_target_level", 3)),
                levels=sorted(levels, key=lambda lv: lv.level_number),
            )
        )

    dimensions.sort(key=lambda dim: dim.code)

    return MaturityModel(
        name=raw.get("name", "Reifegradmodell"),
        description=raw.get("description"),
        levels_info=levels_info,
        dimensions=dimensions,
    )


@st.cache_resource
def load_model(path: Path = MODEL_PATH) -> MaturityModel:
    """Lädt das Reifegradmodell aus der JSON-Konfiguration."""
    if not path.exists():
        raise FileNotFoundError(f"Modelldatei nicht gefunden: {path}")
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return _parse_model(raw)


@st.cache_resource
def load_glossary(path: Path = GLOSSARY_PATH):
    """Lädt das Glossar (Liste aus {term, definition})."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
