# core/scoring.py
# Reifegradberechnung und Ist/Soll/Gaps

from typing import Dict, Tuple, Optional, List
from dataclasses import asdict

import numpy as np
import pandas as pd

from .types import MaturityModel, Dimension

# Globale Antwortskala wie im Excel
ANSWER_OPTIONS = [
    "Vollständig",
    "In den meisten Fällen",
    "In ein paar Fällen",
    "Gar nicht",
    "Nicht anwendbar",
]

ANSWER_SCORES: Dict[str, float] = {
    "Vollständig": 1.0,
    "In den meisten Fällen": 0.75,
    "In ein paar Fällen": 0.5,
    "Gar nicht": 0.0,
    # wie im Excel: NA wird nicht negativ gewertet
    "Nicht anwendbar": 1.0,
}

LEVEL_LABELS: Dict[int, str] = {
    1: "initial",
    2: "gemanagt",
    3: "definiert",
    4: "quantitativ gemanagt",
    5: "optimiert",
}


def answer_to_score(answer: Optional[str]) -> Optional[float]:
    if answer is None:
        return None
    return ANSWER_SCORES.get(answer)


def round_to_quarter(x: float) -> float:
    """Rundet auf 0,25-Schritte."""
    return round(x * 4) / 4.0


def compute_dimension_score(
    dimension: Dimension,
    answers: Dict[str, str],
) -> Tuple[Optional[float], Dict[int, Optional[float]]]:
    """
    Berechnet den Ist-Reifegrad einer Dimension.

    Rückgabe:
    - Gesamt-Score (0..5, auf 0.25 gerundet) oder None
    - Dictionary level_number -> Mittelwert der Antworten
    """
    level_means: Dict[int, Optional[float]] = {}

    # Mittelwert je Stufe berechnen
    for level in dimension.levels:
        scores: List[float] = []
        for q in level.questions:
            s = answer_to_score(answers.get(q.id))
            if s is not None:
                scores.append(s)

        if scores:
            level_means[level.level_number] = float(np.mean(scores))
        else:
            level_means[level.level_number] = None

    # Hierarchische Aggregation
    full_levels = 0
    partial = 0.0
    first_partial = False

    for lvl in sorted(level_means.keys()):
        m = level_means[lvl]
        if m is None:
            break

        if m >= 0.99:  # vollständig erfüllt
            full_levels += 1
        else:
            partial = m
            first_partial = True
            break

    if full_levels == 0 and not first_partial:
        # keine Antworten vorhanden
        return None, level_means

    score = full_levels + partial
    score = max(0.0, min(5.0, score))
    score = round_to_quarter(score)
    return score, level_means


def level_from_score(score: float) -> int:
    """Mappt numerischen Score auf Reifegradstufe 1–5."""
    lvl = int(round(max(0.0, min(5.0, score))))
    return max(1, min(5, lvl))


def compute_results(
    model: MaturityModel,
    answers: Dict[str, str],
    global_target_level: int,
    dimension_targets: Dict[str, int],
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    """
    Berechnet:
    - df_dim: Reifegrad je Dimension (Ist, Soll, Gap)
    - df_cat: gemittelte Werte je Kategorie (TD/OG)
    - overall: Kennzahlen zum Gesamt-Reifegrad
    """
    rows = []
    cat_scores: Dict[str, List[float]] = {}

    for dim in model.dimensions:
        ist_score, _ = compute_dimension_score(dim, answers)

        ist_val = float(ist_score) if ist_score is not None else np.nan

        # Dimension-spezifischer Override > globales Ziel > Default
        target_lvl = int(
            dimension_targets.get(
                dim.code,
                global_target_level if global_target_level else dim.default_target_level,
            )
        )

        gap = target_lvl - ist_val if not np.isnan(ist_val) else np.nan
        ist_level = level_from_score(ist_val) if not np.isnan(ist_val) else np.nan
        ist_text = LEVEL_LABELS.get(ist_level, "") if not np.isnan(ist_level) else ""

        rows.append(
            {
                "Code": dim.code,
                "Name": dim.name,
                "Kategorie": dim.category,
                "Beschreibung": dim.description or "",
                "Ist": ist_val,
                "Ist_Stufe": ist_level,
                "Ist_Text": ist_text,
                "Soll": float(target_lvl),
                "Gap": gap,
            }
        )

        if not np.isnan(ist_val):
            cat_scores.setdefault(dim.category, []).append(ist_val)

    df_dim = pd.DataFrame(rows)

    cat_rows = []
    for cat, vals in cat_scores.items():
        if not vals:
            continue
        m = float(np.mean(vals))
        lvl = level_from_score(m)
        cat_rows.append(
            {
                "Kategorie": cat,
                "Ist": m,
                "Ist_Stufe": lvl,
                "Ist_Text": LEVEL_LABELS.get(lvl, ""),
            }
        )

    df_cat = pd.DataFrame(cat_rows)

    overall_ist = float(df_dim["Ist"].mean()) if not df_dim.empty else np.nan
    overall = {
        "overall_ist": overall_ist,
        "overall_ist_level": level_from_score(overall_ist)
        if not np.isnan(overall_ist)
        else np.nan,
        "overall_ist_text": LEVEL_LABELS.get(level_from_score(overall_ist), "")
        if not np.isnan(overall_ist)
        else "",
        "overall_target": float(global_target_level),
    }

    return df_dim, df_cat, overall
