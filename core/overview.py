# core/overview.py
from __future__ import annotations

from typing import Dict, Any, Optional

import pandas as pd

from .scoring import compute_dimension_maturity


def build_overview_table(
    model: Dict[str, Any],
    answers: Dict[str, str],
    global_target_level: float = 3.0,
    per_dimension_targets: Optional[Dict[str, float]] = None,
    priorities: Optional[Dict[str, Dict[str, str]]] = None,
) -> pd.DataFrame:
    """
    Baut eine DataFrame-Übersicht über alle Dimensionen.

    Spalten:
    - code
    - name
    - category (TD/OG)
    - ist_level
    - target_level
    - gap
    - priority
    - action
    - timeframe
    """

    per_dimension_targets = per_dimension_targets or {}
    priorities = priorities or {}

    rows = []

    for dim in model.get("dimensions", []):
        code = dim["code"]
        name = dim["name"]
        category = dim.get("category", "")

        ist_level = compute_dimension_maturity(dim, answers)

        # Ziel-Reifegrad: Dimension-spezifisch > global > default aus Modell
        if code in per_dimension_targets:
            target_level = float(per_dimension_targets[code])
        elif global_target_level is not None:
            target_level = float(global_target_level)
        else:
            target_level = float(dim.get("default_target_level", 3))

        gap = target_level - ist_level

        prio_info = priorities.get(code, {})
        row = {
            "code": code,
            "name": name,
            "category": category,
            "ist_level": float(ist_level),
            "target_level": float(target_level),
            "gap": float(gap),
            "priority": prio_info.get("priority", ""),
            "action": prio_info.get("action", ""),
            "timeframe": prio_info.get("timeframe", ""),
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # sinnvolle Sortierung: erst TD, dann OG, innerhalb nach Code
    if not df.empty:
        df = df.sort_values(by=["category", "code"]).reset_index(drop=True)

    return df
