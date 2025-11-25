# core/types.py
# Dataklassen für das Reifegradmodell

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Question:
    """Eine einzelne Kontrollfrage zu einer Reifegradstufe."""
    id: str
    text: str
    help_text: Optional[str] = None


@dataclass
class Level:
    """Eine Reifegradstufe (1–5) innerhalb einer Dimension."""
    level_number: int
    name: str
    questions: List[Question] = field(default_factory=list)


@dataclass
class Dimension:
    """Eine Dimension/Subdimension des Reifegradmodells (z. B. TD1.1)."""
    code: str
    name: str
    category: str  # z. B. "TD" oder "OG"
    description: Optional[str] = None
    default_target_level: int = 3
    levels: List[Level] = field(default_factory=list)


@dataclass
class MaturityModel:
    """Das komplette Reifegradmodell (z. B. NIRO TD-Reifegradmodell)."""
    name: str
    description: Optional[str]
    levels_info: Dict[int, str]
    dimensions: List[Dimension] = field(default_factory=list)
