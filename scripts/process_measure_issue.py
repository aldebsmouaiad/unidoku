from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Tuple

MEASURES_FILE = Path("data/measures.json")

MEASURE_HEADING = "### measure_text"
DIMENSION_HEADING = "### dimension_code"


def normalize_measure_text(text: str) -> str:
    """Normalisiert Leerzeichen und trimmt den Text."""
    return " ".join((text or "").split()).strip()


def parse_section(body: str, heading: str, next_heading: str | None = None) -> str:
    """
    Extrahiert einen Abschnitt aus dem Issue-Body.
    Erwartet z. B.:

    ### measure_text
    Text ...

    ### dimension_code
    TD1.1
    """
    if next_heading:
        pattern = rf"{re.escape(heading)}\s*(.*?)\s*{re.escape(next_heading)}"
    else:
        pattern = rf"{re.escape(heading)}\s*(.*)$"

    match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"Abschnitt '{heading}' nicht gefunden oder leer.")

    return normalize_measure_text(match.group(1))


def parse_issue_body(body: str) -> Tuple[str, str]:
    """
    Liest measure_text und dimension_code aus dem Issue-Body.
    """
    body = body or ""

    measure_text = parse_section(body, MEASURE_HEADING, DIMENSION_HEADING)
    dimension_code = parse_section(body, DIMENSION_HEADING, None)

    validate_measure_text(measure_text)
    validate_dimension_code(dimension_code)

    return measure_text, dimension_code


def validate_measure_text(text: str) -> None:
    if not text:
        raise ValueError("measure_text ist leer.")
    if len(text) < 3:
        raise ValueError("measure_text ist zu kurz (min. 3 Zeichen).")
    if len(text) > 240:
        raise ValueError("measure_text ist zu lang (max. 240 Zeichen).")


def validate_dimension_code(code: str) -> None:
    if not code:
        raise ValueError("dimension_code ist leer.")
    if len(code) > 20:
        raise ValueError("dimension_code ist zu lang.")
    # Erlaubt z. B. TD1.1, OG2.3, TD10.12
    if not re.fullmatch(r"[A-Za-z]{1,5}\d+(?:[.\-_]\d+)*", code):
        raise ValueError(f"Ungültiger dimension_code: {code}")


def load_measures() -> dict:
    """
    Lädt data/measures.json. Falls die Datei fehlt oder ungültig ist,
    wird ein leeres Dict zurückgegeben.
    """
    if not MEASURES_FILE.exists():
        return {}

    try:
        data = json.loads(MEASURES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"{MEASURES_FILE} enthält ungültiges JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"{MEASURES_FILE} muss ein JSON-Objekt/Dictionay sein.")

    # Nur Listenwerte akzeptieren; bei anderem Typ leere Liste erzwingen
    cleaned: dict[str, list[str]] = {}
    for key, value in data.items():
        key_str = str(key).strip()
        if not key_str:
            continue

        if isinstance(value, list):
            cleaned[key_str] = [normalize_measure_text(str(v)) for v in value if str(v).strip()]
        else:
            cleaned[key_str] = []

    return cleaned


def save_measures(data: dict) -> None:
    """
    Speichert data/measures.json formatiert und UTF-8 sauber.
    """
    MEASURES_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEASURES_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def add_measure_if_new(data: dict, dimension_code: str, measure_text: str) -> bool:
    """
    Fügt eine Maßnahme hinzu, falls sie unter dem Code noch nicht existiert.
    Vergleich ist case-insensitive und whitespace-normalisiert.
    """
    existing = data.get(dimension_code, [])
    if not isinstance(existing, list):
        existing = []

    existing_norm = {
        normalize_measure_text(str(item)).lower()
        for item in existing
        if normalize_measure_text(str(item))
    }

    normalized_candidate = normalize_measure_text(measure_text)
    if normalized_candidate.lower() in existing_norm:
        data[dimension_code] = existing
        return False

    existing.append(normalized_candidate)
    data[dimension_code] = existing
    return True


def print_summary(added: bool, dimension_code: str, measure_text: str) -> None:
    print("----- process_measure_issue.py -----")
    print(f"Dimension: {dimension_code}")
    print(f"Measure:   {measure_text}")
    print(f"Added:     {'1' if added else '0'}")
    print("-----------------------------------")


def main() -> int:
    issue_body = os.environ.get("ISSUE_BODY", "")
    if not issue_body.strip():
        print("Fehler: Umgebungsvariable ISSUE_BODY fehlt oder ist leer.", file=sys.stderr)
        return 1

    try:
        measure_text, dimension_code = parse_issue_body(issue_body)
        measures = load_measures()
        added = add_measure_if_new(measures, dimension_code, measure_text)

        if added:
            save_measures(measures)

        print_summary(added, dimension_code, measure_text)
        return 0

    except Exception as e:
        print(f"Fehler beim Verarbeiten des Issues: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())