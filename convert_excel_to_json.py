"""
convert_excel_to_json.py

Liest das Excel-Tool 'NIRO_RGM_TD_Erhebungstool.xlsx' ein und
erzeugt daraus die JSON-Konfigurationsdatei
'data/models/niro_td_model.json' für die Streamlit-App.

Logik:
- alle Arbeitsblätter, deren Name wie 'TD1.1', 'TD2.3', 'OG1.1' usw. aussieht,
  werden als Dimensionen interpretiert
- Dimensonsname: Zeile 6, Spalte C (Index [5, 2])
- Beschreibung (Zweck): Zeile 7, Spalte C (Index [6, 2])
- Fragen:
    * stehen in Spalte C (Index 2)
    * die zugehörige Reifegradstufe steht in Spalte B (Index 1)
    * wenn in Spalte B kein Wert steht, wird die zuletzt
      gesehene Stufe nach unten "durchvererbt"
    * alle Zeilen oberhalb Zeile 15 werden ignoriert (Header/Erklärungen)
"""

import json
import math
import re
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

# Pfade anpassen, falls dein Projekt woanders liegt
BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "NIRO_RGM_TD_Erhebungstool.xlsx"
OUTPUT_PATH = BASE_DIR / "data" / "models" / "niro_td_model.json"

# Reifegrad-Bezeichnungen
LEVEL_LABELS: Dict[int, str] = {
    1: "initial",
    2: "gemanagt",
    3: "definiert",
    4: "quantitativ gemanagt",
    5: "optimiert",
}


def extract_dimension_from_sheet(excel_path: Path, sheet_name: str):
    """
    Liest EIN Dimensions-Blatt (z. B. 'TD1.1') aus dem Excel
    und extrahiert:
      - Dimensonsname
      - Beschreibung (Zweck)
      - Fragen je Reifegradstufe

    Rückgabe:
      (dim_name, description, level_questions)
      level_questions: dict[int -> List[str]]
    """
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

    # Code kommt aus dem Blattnamen, Kategorie aus dem Präfix
    dim_code = sheet_name
    category = "TD" if sheet_name.startswith("TD") else "OG"

    # Dimensionstitel & Zweck (siehe Aufbau im Excel)
    name_cell = df.iloc[5, 2]  # Zeile 6, Spalte C
    desc_cell = df.iloc[6, 2]  # Zeile 7, Spalte C

    dim_name = str(name_cell).strip() if isinstance(name_cell, str) else dim_code
    description = str(desc_cell).strip() if isinstance(desc_cell, str) else ""

    # Fragen ab ca. Zeile 15 (Index 14) nach unten durchsuchen
    last_level = None
    level_questions: Dict[int, List[str]] = {}

    for row in range(len(df)):
        text = df.iloc[row, 2]      # Spalte C: Fragentext
        lvl_cell = df.iloc[row, 1]  # Spalte B: "Zu Reifegrad"

        # Neue Stufe beginnt, wenn in Spalte B eine Zahl (1–5) steht
        if isinstance(lvl_cell, (int, float)) and not math.isnan(lvl_cell):
            last_level = int(lvl_cell)

        # Nur echte Fragentexte berücksichtigen
        if isinstance(text, str) and text.strip():
            # Header- / Erklärzeilen überspringen
            if row < 14:
                continue
            if "Zu Reifegrad" in text:
                continue  # Zeilenüberschrift

            if last_level is None:
                # Falls noch keine Stufe gesetzt ist, ignorieren
                continue

            # Frage dem zuletzt gesetzten Level zuordnen
            level_questions.setdefault(last_level, []).append(text.strip())

    return dim_code, category, dim_name, description, level_questions


def build_full_model(excel_path: Path) -> dict:
    """
    Erzeugt das komplette Modell-Dikt mit allen TD-/OG-Dimensionen,
    so wie es später von der Streamlit-App erwartet wird.
    """
    xls = pd.ExcelFile(excel_path)

    # Nur Blätter wie 'TD1.1', 'TD2.3', 'OG1.1', ...
    dim_sheets = [
        name
        for name in xls.sheet_names
        if re.match(r"^(TD|OG)\d+\.\d+$", name)
    ]

    dimensions = []

    for sheet_name in dim_sheets:
        (
            dim_code,
            category,
            dim_name,
            description,
            level_questions,
        ) = extract_dimension_from_sheet(excel_path, sheet_name)

        # 5 Reifegradstufen anlegen, auch wenn eine Stufe keine Fragen hat
        levels = []
        for lvl in range(1, 6):
            questions_texts = level_questions.get(lvl, [])
            question_objs = []

            for i, q_text in enumerate(questions_texts, start=1):
                q_id = f"{dim_code}-L{lvl}-Q{i}"
                question_objs.append(
                    {
                        "id": q_id,
                        "text": q_text,
                    }
                )

            levels.append(
                {
                    "level_number": lvl,
                    "name": LEVEL_LABELS.get(lvl, f"Stufe {lvl}"),
                    "questions": question_objs,
                }
            )

        dimensions.append(
            {
                "code": dim_code,
                "name": dim_name,
                "category": category,
                "description": description,
                # Standardziel: 3 (definiert) – kann die App später überschreiben
                "default_target_level": 3,
                "levels": levels,
            }
        )

    # Sortierung nach Code für stabile Reihenfolge (TD1.1, TD1.2, ...)
    dimensions.sort(key=lambda d: d["code"])

    model = {
        "name": "NIRO Reifegradmodell Technische Dokumentation",
        "description": (
            "Automatisch aus der Excel-Datei 'NIRO_RGM_TD_Erhebungstool.xlsx' "
            "erzeugte Modellkonfiguration."
        ),
        "levels_info": {str(k): v for k, v in LEVEL_LABELS.items()},
        "dimensions": dimensions,
    }

    return model


def main():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"Excel-Datei nicht gefunden: {EXCEL_PATH}\n"
            "Bitte prüfe den Pfad oder kopiere die Datei in den Projektordner."
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    model = build_full_model(EXCEL_PATH)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)

    print(f"JSON-Modell mit {len(model['dimensions'])} Dimension(en) erzeugt:")
    print(f" -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
