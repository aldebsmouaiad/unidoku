# core/types.py
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Question:
    id: str
    text: str
    help_text: Optional[str] = None


@dataclass
class Level:
    level_number: int
    name: str
    questions: List[Question]


@dataclass
class Dimension:
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
    code: str
    name: str
    category: str
    ist_level: float
    soll_level: float
    gap: float
    priority: Optional[str] = None
    action: Optional[str] = None
    timeframe: Optional[str] = None

