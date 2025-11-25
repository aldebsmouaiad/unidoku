# core/export_csv.py
# CSV-Generierung

from typing import Optional

import pandas as pd
import io


def build_export_dataframe(
    df_dim: pd.DataFrame,
    priorities_df: Optional[pd.DataFrame],
    org: str,
    assessor: str,
    date_str: str,
    target_label: str,
) -> pd.DataFrame:
    """Fügt Metadaten & Prioritäten zu den Dimensionsergebnissen hinzu."""
    base = df_dim.copy()

    if priorities_df is not None and not priorities_df.empty:
        cols = ["Code", "Priorität", "Maßnahme", "Zeitraum"]
        tmp = priorities_df[cols].copy()
        base = base.merge(tmp, on="Code", how="left")
    else:
        base["Priorität"] = ""
        base["Maßnahme"] = ""
        base["Zeitraum"] = ""

    base.insert(0, "Organisation", org)
    base.insert(1, "Bewertet_von", assessor)
    base.insert(2, "Datum", date_str)
    base.insert(3, "Globales_Ziel_Label", target_label)

    return base


def export_csv_bytes(df_export: pd.DataFrame) -> bytes:
    """Konvertiert DataFrame in CSV-Bytes (UTF-8, ; als Trenner)."""
    buffer = io.StringIO()
    df_export.to_csv(buffer, index=False, sep=";")
    return buffer.getvalue().encode("utf-8")
