from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class MaturityAverage:
    value: Optional[float]
    count: int


CURRENT_LEVEL_COLUMNS = (
    "ist_level",
    "Ist-Reifegrad",
    "Current maturity level",
    "current_level",
    "ist",
    "Ist",
    "IST",
)

ASSESSED_COLUMNS = (
    "answered",
    "Bewertet",
    "Assessed",
    "assessed",
)


def _pick_first_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _prefix_mask(df: pd.DataFrame, prefix: str) -> pd.Series:
    prefix = str(prefix or "").strip().upper()
    if df is None or df.empty:
        return pd.Series(dtype=bool)

    category_col = _pick_first_col(df, ("category", "Kategorie"))
    if category_col:
        categories = df[category_col].astype(str).fillna("").str.strip().str.upper()
        mask = categories.eq(prefix)
        if bool(mask.any()):
            return mask

    code_col = _pick_first_col(df, ("code", "Code", "Kürzel", "Kuerzel"))
    if not code_col:
        return pd.Series([False] * len(df), index=df.index)

    extracted = (
        df[code_col]
        .astype(str)
        .fillna("")
        .str.strip()
        .str.upper()
        .str.extract(r"^([A-Z]+)", expand=False)
        .fillna("")
    )
    return extracted.eq(prefix)


def _current_levels(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=float)

    level_col = _pick_first_col(df, CURRENT_LEVEL_COLUMNS)
    if not level_col:
        return pd.Series(dtype=float)

    levels = pd.to_numeric(df[level_col], errors="coerce")
    finite_mask = levels.apply(lambda value: pd.notna(value) and math.isfinite(float(value)))
    return levels.where(finite_mask)


def _assessed_mask(df: pd.DataFrame, levels: pd.Series) -> pd.Series:
    assessed_col = _pick_first_col(df, ASSESSED_COLUMNS)
    if assessed_col:
        raw = df[assessed_col]
        if raw.dtype == bool:
            return raw.fillna(False).astype(bool)

        text = raw.astype(str).fillna("").str.strip().str.lower()
        true_values = {"true", "1", "yes", "ja", "y", "j", "bewertet", "assessed"}
        false_values = {"false", "0", "no", "nein", "n", "", "nan", "none", "null", "undefined"}

        numeric = pd.to_numeric(raw, errors="coerce")
        return text.isin(true_values) | (~text.isin(false_values) & numeric.fillna(0).astype(float).ne(0))

    # Fallback wie in der Gesamtübersicht: Bewertet sind nur Dimensionen mit Ist-Reifegrad > 0.
    return levels.notna() & levels.astype(float).gt(0)


def _assessed_current_levels(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=float)

    levels = _current_levels(df)
    if levels.empty:
        return pd.Series(dtype=float)

    mask = _assessed_mask(df, levels)
    return levels[mask & levels.notna()].astype(float)


def _average_from_levels(levels: pd.Series) -> MaturityAverage:
    if levels.empty:
        return MaturityAverage(value=None, count=0)
    return MaturityAverage(value=float(levels.mean()), count=int(levels.count()))


def _valid_current_levels_for_prefix(df: pd.DataFrame, prefix: str) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=float)
    return _assessed_current_levels(df[_prefix_mask(df, prefix)].copy())


def calculate_current_maturity_average(df: pd.DataFrame, prefix: Optional[str] = None) -> MaturityAverage:
    """
    Berechnet Durchschnittswerte nur aus bewerteten Ist-Reifegrad-Werten.

    Wenn eine Bewertet-/answered-Spalte vorhanden ist, steuert sie die Auswahl.
    Andernfalls gilt wie in der Gesamtübersicht: Ist-Reifegrad > 0 ist bewertet;
    0, None, NaN, leerer String, fehlende Werte und "undefined" gehen nicht ein.
    Ohne Prefix wird der Gesamtdurchschnitt ausschließlich aus TD und OG gebildet.
    """
    if df is None or df.empty:
        return MaturityAverage(value=None, count=0)

    d = df.copy()
    if prefix:
        return _average_from_levels(_valid_current_levels_for_prefix(d, prefix))

    td_levels = _valid_current_levels_for_prefix(d, "TD")
    og_levels = _valid_current_levels_for_prefix(d, "OG")
    return _average_from_levels(pd.concat([td_levels, og_levels], ignore_index=True))


def calculate_current_maturity_averages(df: pd.DataFrame) -> dict[str, MaturityAverage]:
    td_levels = _valid_current_levels_for_prefix(df, "TD")
    og_levels = _valid_current_levels_for_prefix(df, "OG")
    combined = pd.concat([td_levels, og_levels], ignore_index=True)

    return {
        "overall": _average_from_levels(combined),
        "td": _average_from_levels(td_levels),
        "og": _average_from_levels(og_levels),
    }
