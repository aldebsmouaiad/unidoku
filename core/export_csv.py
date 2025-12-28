# core/export_csv.py
from typing import Optional

import pandas as pd
import io


def _na_to_text(x) -> object:
    """
    Wandelt NaN/Inf in ein Excel-nahes Textlabel um.
    Excel zeigt in solchen Fällen typischerweise n.a./#N/A.
    Für CSV nutzen wir "n.a.".
    """
    try:
        if pd.isna(x):
            return "n.a."
    except Exception:
        pass
    return x


def build_export_dataframe(
    df_dim: pd.DataFrame,
    org: str,
    assessor: str,
    date_str: str,
    target_label: str,
    area: str = "",  # neu: Bereich (optional, um Call-Sites nicht sofort zu brechen)
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

    Neue Excel-Logik-Anpassungen:
    - Metadaten-Spalte "Bereich" wird ergänzt.
    - n/a (NaN aus scoring) wird als "n.a." exportiert (statt leer/nan).
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
            prio_col = f"{col}_prio"
            if prio_col in base.columns:
                base[col] = base[prio_col].fillna(base[col])
                base.drop(columns=[prio_col], inplace=True)

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

    # n.a. Handling (NaN aus scoring) -> "n.a." im CSV
    # Wichtig: Ziel_Level bleibt i.d.R. numerisch; Ist_Level/Gap können n.a. sein.
    for col in ["Ist_Level", "Gap"]:
        if col in export_df.columns:
            export_df[col] = export_df[col].apply(_na_to_text)

    # Metadaten vorne einfügen (Reihenfolge Excel-nah)
    export_df.insert(0, "Organisation", org)
    export_df.insert(1, "Bereich", area)
    export_df.insert(2, "Bewertet_von", assessor)
    export_df.insert(3, "Datum", date_str)
    export_df.insert(4, "Globales_Ziel_Label", target_label)

    return export_df


def export_csv_bytes(df_export: pd.DataFrame) -> bytes:
    """Konvertiert DataFrame in CSV-Bytes (UTF-8, ; als Trenner)."""
    buffer = io.StringIO()
    df_export.to_csv(buffer, index=False, sep=";")
    return buffer.getvalue().encode("utf-8")
