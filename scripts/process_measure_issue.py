from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MEASURES_FILE = Path("data/measures.json")


def normalize_measure_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def parse_section(body: str, heading: str, next_heading: str | None = None) -> str:
    if next_heading:
        pattern = rf"{re.escape(heading)}\s*(.*?)\s*{re.escape(next_heading)}"
    else:
        pattern = rf"{re.escape(heading)}\s*(.*)$"

    match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"Abschnitt '{heading}' nicht gefunden oder leer.")

    return normalize_measure_text(match.group(1))


def parse_issue_body(body: str) -> tuple[str, str]:
    body = body or ""

    measure_text = parse_section(body, "### measure_text", "### dimension_code")
    dimension_code = parse_section(body, "### dimension_code", None)

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
    if not re.fullmatch(r"[A-Za-z]{1,5}\d+(?:[.\-_]\d+)*", code):
        raise ValueError(f"Ungültiger dimension_code: {code}")


def load_measures() -> dict:
    if not MEASURES_FILE.exists():
        return {}

    try:
        data = json.loads(MEASURES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"{MEASURES_FILE} enthält ungültiges JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"{MEASURES_FILE} muss ein JSON-Objekt sein.")

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
    MEASURES_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEASURES_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def add_measure_if_new(data: dict, dimension_code: str, measure_text: str) -> bool:
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

        print(f"Dimension: {dimension_code}")
        print(f"Measure: {measure_text}")
        print(f"Added: {'1' if added else '0'}")
        return 0

    except Exception as e:
        print(f"Fehler beim Verarbeiten des Issues: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())