# core/export_csv.py
from typing import Optional

import pandas as pd
import io


def build_export_dataframe(
    df_dim: pd.DataFrame,
    org: str,
    assessor: str,
    date_str: str,
    target_label: str,
    priorities_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Baut ein Export-DataFrame auf Basis der Übersichts-Tabelle (build_overview_table).

    Erwartet df_dim mit Spalten:
      - code, name, category, ist_level, target_level, gap
      - optional: priority, action, timeframe

    Optional können Prioritäten aus einer separaten Tabelle (priorities_df)
    übernommen werden. Diese darf entweder Spaltennamen in Englisch
    (code, priority, action, timeframe) oder Deutsch (Code, Priorität,
    Maßnahme, Zeitraum) haben.
    """
    base = df_dim.copy()

    # Sicherstellen, dass die "internen" Priority-Spalten existieren
    for col in ["priority", "action", "timeframe"]:
        if col not in base.columns:
            base[col] = ""

    # Falls eine separate Prioritäten-Tabelle kommt, diese integrieren
    if priorities_df is not None and not priorities_df.empty:
        tmp = priorities_df.copy()

        # Einheitliche Spaltennamen herstellen
        rename_map = {
            "Code": "code",
            "Priorität": "priority",
            "Maßnahme": "action",
            "Zeitraum": "timeframe",
        }
        tmp = tmp.rename(columns=rename_map)

        # Nur relevante Spalten behalten, wenn vorhanden
        keep_cols = [c for c in ["code", "priority", "action", "timeframe"] if c in tmp.columns]
        tmp = tmp[keep_cols].drop_duplicates(subset=["code"])

        # Merge über "code"
        base = base.merge(tmp, on="code", how="left", suffixes=("", "_prio"))

        # Falls es Überschneidungen gibt, prio-Spalten bevorzugen
        for col in ["priority", "action", "timeframe"]:
            if f"{col}_prio" in base.columns:
                base[col] = base[f"{col}_prio"].fillna(base[col])
                base.drop(columns=[f"{col}_prio"], inplace=True)

    # Jetzt ins "schöne" Export-Schema umbenennen
    export_df = base.rename(
        columns={
            "code": "Code",
            "name": "Dimension",
            "category": "Kategorie",
            "ist_level": "Ist_Level",
            "target_level": "Ziel_Level",
            "gap": "Gap",
            "priority": "Priorität",
            "action": "Maßnahme",
            "timeframe": "Zeitraum",
        }
    )

    # Metadaten vorne einfügen
    export_df.insert(0, "Organisation", org)
    export_df.insert(1, "Bewertet_von", assessor)
    export_df.insert(2, "Datum", date_str)
    export_df.insert(3, "Globales_Ziel_Label", target_label)

    return export_df


def export_csv_bytes(df_export: pd.DataFrame) -> bytes:
    """Konvertiert DataFrame in CSV-Bytes (UTF-8, ; als Trenner)."""
    buffer = io.StringIO()
    df_export.to_csv(buffer, index=False, sep=";")
    return buffer.getvalue().encode("utf-8")
