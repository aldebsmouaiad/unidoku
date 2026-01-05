# core/types.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Question:
    """
    Eine "Frage" entspricht i. d. R. der Kontrollfrage inkl. ggf. Kriterien/Unterpunkten im help_text.
    """
    id: str
    text: str
    help_text: Optional[str] = None


@dataclass
class Level:
    """
    Ein Reifegrad-Level innerhalb einer Dimension/Subdimension.

    Neu (Excel 20251209):
    - benefit_text: "Nutzen bei Erreichen der Stufe"
    - comment_hint: "Kommentar/Hinweis"

    Optional bleiben die Felder, damit ältere Modelle/JSONs weiterhin funktionieren.
    """
    level_number: int
    name: str
    questions: List[Question]

    # optionaler Level-Metatext (je nach Modellstruktur)
    implementation_text: Optional[str] = None  # z. B. "Umsetzung"
    benefit_text: Optional[str] = None         # neu: Nutzen bei Erreichen der Stufe
    comment_hint: Optional[str] = None         # neu: Kommentar/Hinweis


@dataclass
class Dimension:
    """
    Eine Dimension/Subdimension im Modell.
    """
    code: str
    name: str
    category: str   # "TD" oder "OG"
    description: str
    default_target_level: int
    levels: List[Level]


@dataclass
class MaturityModel:
    name: str
    description: str
    levels_info: Dict[str, str]      # z.B. {"1": "initial", ...}
    dimensions: List[Dimension]


@dataclass
class DimensionOverviewRow:
    """
    Optionales Typ-Objekt für Übersichten (wird nicht zwingend genutzt, aber sauber gehalten).
    """
    code: str
    name: str
    category: str
    ist_level: float
    soll_level: float
    gap: float
    priority: Optional[str] = None
    action: Optional[str] = None
    timeframe: Optional[str] = None
