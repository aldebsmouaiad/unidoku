# core/scoring.py
from __future__ import annotations

import math
from typing import Dict, Any, List, Optional

from core.types import Dimension as DimensionDC


# Antwort-Skala (Text -> numerischer Score)
# Neue Excel-Logik: "Nicht anwendbar" => None (aus dem Nenner entfernen)
ANSWER_SCORES: Dict[str, Optional[float]] = {
    "Vollständig": 1.0,
    "In den meisten Fällen": 0.75,
    "In ein paar Fällen": 0.5,
    "Gar nicht": 0.0,
    "Nicht anwendbar": None,
}


def _iter_levels(dimension: DimensionDC | Dict[str, Any]):
    """
    Liefert eine sortierte Liste von Level-Objekten (egal ob Dataclass oder Dict).
    """
    if isinstance(dimension, DimensionDC):
        levels = sorted(dimension.levels, key=lambda lvl: lvl.level_number)
        for lvl in levels:
            yield {
                "level_number": lvl.level_number,
                "questions": [{"id": q.id} for q in lvl.questions],
            }
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
    Berechnet den Ist-Reifegrad einer Dimension (neue Excel-Logik 20251209):

    - "Nicht anwendbar" wird NICHT als erfüllt gezählt, sondern aus dem Nenner entfernt.
    - Unbeantwortet (None) zählt als 0.0 (wie "Gar nicht"), damit nichts schöngerechnet wird.
    - Wenn Level 1 ausschließlich NA ist => Ergebnis = NaN (entspricht n/a/#N/A).
    - Gating: sobald ein Level nicht vollständig erfüllt ist, wird abgebrochen.
    - Rundung: immer ABRUNDEN auf 0.25-Schritte.
    """
    levels = list(_iter_levels(dimension))
    if not levels:
        return 0.0

    fully_reached = 0
    partial_fraction = 0.0
    partial_found = False

    for level in levels:
        q_ids = [q["id"] for q in level["questions"]]

        # Scores dieses Levels (anwendbar)
        applicable_scores: List[float] = []

        for q_id in q_ids:
            ans = answers.get(q_id)

            # Unbeantwortet zählt als 0.0 (wichtig: nicht "continue")
            if ans is None:
                applicable_scores.append(0.0)
                continue

            # Text-Antworten (Single-Choice)
            score = ANSWER_SCORES.get(str(ans))

            # Nicht anwendbar -> None -> aus Nenner entfernen
            if score is None and str(ans) == "Nicht anwendbar":
                continue

            # Unbekannter Text -> konservativ 0.0
            if score is None:
                score = 0.0

            applicable_scores.append(score)

        # Wenn gar keine anwendbaren Fragen im Level übrig bleiben => Level ist "n.a."
        if not applicable_scores:
            if level["level_number"] == 1:
                return float("nan")  # Excel: Stufe 1 n.a. => gesamte Subdimension n.a.
            break

        avg_score = sum(applicable_scores) / len(applicable_scores)

        if avg_score >= 0.99:
            fully_reached += 1
        else:
            partial_fraction = avg_score
            partial_found = True
            break

    maturity = float(fully_reached)
    if partial_found:
        maturity += partial_fraction

    # Excel neu: ROUNDDOWN auf 0.25-Schritte
    maturity = math.floor(maturity * 4.0) / 4.0
    return maturity
