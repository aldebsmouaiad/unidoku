"""
Kurzes Testskript, um die Google Sheets Verbindung mit einem Service-Account zu prüfen.

Sichere Nutzung:
- Lege die Service-Account-JSON in die Projektwurzel als `test_credentials.json` (oder einen sicheren Pfad) ab.
- Teile die Google Spreadsheet-Datei mit der `client_email` aus der JSON.
- Setze die Spreadsheet-ID (nicht ganze URL) in SHEET_ID.

Installation (einmalig):
    pip install gspread google-auth

Ausführung:
    python3 tools/test_gsheets_connection.py

Wichtig: Niemals sensiblen JSON-Inhalt in öffentlichen Chats oder Repositories posten. Falls die JSON bereits öffentlich wurde, widerrufe den Key sofort in der GCP-Konsole und erstelle einen neuen.
"""

import json
import sys
from pathlib import Path

try:
    from google.oauth2.service_account import Credentials
    import gspread
except Exception as e:
    print("Fehler: Benötigte Pakete fehlen. Installiere sie mit:\n  pip install gspread google-auth")
    sys.exit(1)

CREDENTIALS_FILE = Path("test_credentials.json")
# Trage hier die Spreadsheet-ID (nur die ID, nicht die ganze URL) ein:
SHEET_ID = "1IEAfD_Asm-g6YhWXIg2J3WfzHTf2iha1X2uhMk-KrkE"

if not CREDENTIALS_FILE.exists():
    print(f"Bitte lege die Service-Account-JSON als '{CREDENTIALS_FILE}' ab und führe das Skript erneut aus.")
    sys.exit(1)

try:
    with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
        info = json.load(f)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)

    sh = gc.open_by_key(SHEET_ID)
    sheets = [ws.title for ws in sh.worksheets()]
    print("Verbindung erfolgreich. Gefundene Tabs:")
    for s in sheets:
        print(" -", s)

except Exception as e:
    # Genaue Fehlermeldung ausgeben, aber keine sensiblen Inhalte der Credentials drucken
    print("Fehler beim Verbinden mit Google Sheets:")
    print(repr(e))
    print("\nHinweise:\n - Prüfe, ob die Spreadsheet-Datei mit der 'client_email' aus der Service-Account-JSON geteilt ist.\n - Prüfe, ob die Google Sheets API im Google Cloud Projekt aktiviert ist.\n - Falls die Fehlermeldung '401' lautet: die Freigabe oder der Key ist ungültig/entzogen.")
    sys.exit(1)
