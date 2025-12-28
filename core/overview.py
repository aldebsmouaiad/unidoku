# core/overview.py
from __future__ import annotations

from typing import Dict, Any, Optional, Tuple
import re

import pandas as pd

from .scoring import compute_dimension_maturity


def _infer_category(code: str, category: str) -> str:
    """
    Falls im Modell keine Kategorie gepflegt ist, leiten wir sie aus dem Code ab (z.B. TD / OG).
    """
    if category:
        return category
    m = re.match(r"^([A-Za-z]+)", str(code).strip())
    return m.group(1) if m else ""


def _code_sort_parts(code: str) -> Tuple[str, int, int, int]:
    """
    Natürliche Sortierung für Codes wie:
      TD1.1, TD2.10, OG3.2, ...

    Rückgabe:
      (prefix, n1, n2, n3)
    - prefix: Buchstabenpräfix (TD/OG/...)
    - n1..n3: erste drei Zahlenkomponenten (fehlende -> 0)

    Damit wird TD10.1 korrekt NACH TD2.1 sortiert.
    """
    s = str(code).strip()
    m = re.match(r"^([A-Za-z]+)", s)
    prefix = m.group(1) if m else ""
    nums = [int(x) for x in re.findall(r"\d+", s)]
    while len(nums) < 3:
        nums.append(0)
    return prefix, nums[0], nums[1], nums[2]


def build_overview_table(
    model: Dict[str, Any],
    answers: Dict[str, Any],
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
        category = _infer_category(code, dim.get("category", ""))

        ist_level = compute_dimension_maturity(dim, answers)

        # Ziel-Reifegrad: Dimension-spezifisch > global > default aus Modell
        if code in per_dimension_targets:
            target_level = float(per_dimension_targets[code])
        elif global_target_level is not None:
            target_level = float(global_target_level)
        else:
            target_level = float(dim.get("default_target_level", 3))

        # gap: NaN bleibt NaN (wenn ist_level n/a ist)
        gap = target_level - float(ist_level)

        prio_info = priorities.get(code, {})
        row = {
            "code": str(code),
            "name": str(name),
            "category": str(category),
            "ist_level": float(ist_level),
            "target_level": float(target_level),
            "gap": float(gap),
            "priority": prio_info.get("priority", ""),
            "action": prio_info.get("action", ""),
            "timeframe": prio_info.get("timeframe", ""),
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Sinnvolle Sortierung: erst TD, dann OG, innerhalb numerisch nach Code
    if not df.empty:
        # Kategorie-Order: TD vor OG, Rest danach
        cat_order = {"TD": 0, "OG": 1}
        df["_cat_sort"] = df["category"].map(cat_order).fillna(99).astype(int)

        # Natürliche Codesortierung (TD2.10 nach TD2.2 etc.)
        parts = df["code"].apply(_code_sort_parts)
        df["_code_prefix"] = parts.apply(lambda t: t[0])
        df["_code_n1"] = parts.apply(lambda t: t[1])
        df["_code_n2"] = parts.apply(lambda t: t[2])
        df["_code_n3"] = parts.apply(lambda t: t[3])

        df = (
            df.sort_values(
                by=["_cat_sort", "_code_prefix", "_code_n1", "_code_n2", "_code_n3"],
                ascending=[True, True, True, True, True],
            )
            .drop(columns=["_cat_sort", "_code_prefix", "_code_n1", "_code_n2", "_code_n3"])
            .reset_index(drop=True)
        )

    return df
