# core/scoring.py
from __future__ import annotations

from typing import Dict, Any, List

from core.types import Dimension as DimensionDC

# Antwort-Skala (Text -> numerischer Score)
ANSWER_SCORES: Dict[str, float] = {
    "Vollständig": 1.0,
    "In den meisten Fällen": 0.75,
    "In ein paar Fällen": 0.5,
    "Gar nicht": 0.0,
    "Nicht anwendbar": 1.0,  # wird wie "erfüllt" gewertet
}


def _iter_levels(dimension: DimensionDC | Dict[str, Any]):
    """
    Liefert eine sortierte Liste von Level-Objekten (egal ob Dataclass oder Dict).
    """
    # Fall 1: Dataclass-Variante
    if isinstance(dimension, DimensionDC):
        levels = sorted(dimension.levels, key=lambda lvl: lvl.level_number)
        for lvl in levels:
            yield {
                "level_number": lvl.level_number,
                "questions": [{"id": q.id} for q in lvl.questions],
            }

    # Fall 2: JSON-/Dict-Variante
    else:
        levels_raw = sorted(
            dimension.get("levels", []),
            key=lambda lvl: lvl.get("level_number", 0),
        )
        for lvl in levels_raw:
            yield {
                "level_number": lvl.get("level_number", 0),
                "questions": lvl.get("questions", []),
            }


def compute_dimension_maturity(
    dimension: DimensionDC | Dict[str, Any],
    answers: Dict[str, Any],
) -> float:
    """
    Berechnet den Ist-Reifegrad einer Dimension auf Basis der Antworten.

    Unterstützt:
    - numerische Antworten 1–5 (Slider aus 01_Erhebung.py)
    - Text-Antworten gemäß ANSWER_SCORES.

    Logik:
    - Für jedes Level werden die Fragen gesucht.
    - Antworten werden in einen Score in [0, 1] umgerechnet.
      * Zahl 1..5 -> 0.0..1.0 (1 = gar nicht, 5 = vollständig)
      * Text -> gemäß ANSWER_SCORES
    - Ein Level gilt als "erreicht", wenn der Durchschnitt >= 0.99 ist.
    - Reifegrad = Anzahl vollständig erreichter Levels
      + ggf. Anteil beim ersten nicht vollständig erfüllten Level.
    - Ergebnis wird auf 0.25-Schritte gerundet.
    """
    levels = list(_iter_levels(dimension))
    if not levels:
        return 0.0

    fully_reached = 0
    partial_fraction = 0.0
    partial_found = False

    for level in levels:
        q_ids = [q["id"] for q in level["questions"]]
        scores: List[float] = []

        for q_id in q_ids:
            ans = answers.get(q_id)
            if ans is None:
                continue

            score: float | None

            # Fall A: numerische Skala 1–5 (Slider)
            if isinstance(ans, (int, float)):
                val = float(ans)
                # auf 1..5 begrenzen
                val = max(1.0, min(5.0, val))
                # 1 -> 0.0, 5 -> 1.0
                score = (val - 1.0) / 4.0

            # Fall B: Textskala (Vollständig, Gar nicht, ...)
            else:
                score = ANSWER_SCORES.get(str(ans))

            if score is None:
                continue

            scores.append(score)

        if not scores:
            # keine verwertbaren Antworten für dieses Level -> Abbruch
            break

        avg_score = sum(scores) / len(scores)

        if avg_score >= 0.99:
            fully_reached += 1
        else:
            partial_fraction = avg_score  # 0..1
            partial_found = True
            break

    maturity = float(fully_reached)
    if partial_found:
        maturity += partial_fraction

    # auf 0.25-Schritte runden
    maturity = round(maturity * 4) / 4.0
    return maturity
