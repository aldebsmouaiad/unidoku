import os
import toml
import pandas as pd
from config import (
    GOOGLE_SHEET_ANSWERS,
    GOOGLE_SHEET_PROFILES,
    GOOGLE_SHEET_BEDARFE,
    GOOGLE_SHEET_ANSWERS_FRAGEBOGEN,
    COLUMN_TIMESTAMP,
    COLUMN_PROFILE_ID,
    COLUMN_INDEX,
    COLUMN_ROLE,
    CLUSTER_COLUMNS,
    PATH_QUESTIONNAIRE,
    COLUMN_QUESTION_ID,
    COLUMN_CLUSTER_NUMBER,
    COLUMN_CLUSTER_NAME,
    COLUMN_SUBSCALE,
    COLUMN_QUESTION,
    COLUMN_INVERTED,
)

BASE = os.path.dirname(os.path.dirname(__file__))
SECRETS_PATH = os.path.join(BASE, '.streamlit', 'secrets.toml')
EXAMPLE_DIR = os.path.join(BASE, 'upload_beispiel_dateien')

required_sheets = [GOOGLE_SHEET_PROFILES, GOOGLE_SHEET_ANSWERS, GOOGLE_SHEET_BEDARFE]
optional_sheets = [GOOGLE_SHEET_ANSWERS_FRAGEBOGEN]

print('\n=== Validierung Projekt-Setup (lokal) ===\n')

# 1) secrets.toml prüfen
print('1) .streamlit/secrets.toml')
if not os.path.exists(SECRETS_PATH):
    print('   -> FEHLER: Datei .streamlit/secrets.toml existiert nicht.')
else:
    try:
        data = toml.load(SECRETS_PATH)
        gs = data.get('connections', {}).get('gsheets', {})
        sa = data.get('gcp_service_account', {})
        spreadsheet = gs.get('spreadsheet') if gs else None
        client_email = sa.get('client_email') if sa else None
        print(f'   -> gefunden: {SECRETS_PATH}')
        print(f'      spreadsheet: {spreadsheet}')
        print(f'      client_email: {client_email}')
        if not spreadsheet:
            print('   -> WARNUNG: Kein spreadsheet-URL unter [connections.gsheets].')
        if not client_email:
            print('   -> WARNUNG: Kein client_email unter [gcp_service_account].')
    except Exception as e:
        print('   -> FEHLER beim Lesen von secrets.toml:', e)

# helper
def check_csv(path, sep=';', decimal=','):
    try:
        df = pd.read_csv(path, sep=sep, decimal=decimal, encoding='utf-8')
    except Exception:
        try:
            df = pd.read_csv(path, sep=sep, decimal=decimal, encoding='unicode_escape')
        except Exception as e:
            raise
    return df

# 2) Beispiel-CSV Dateien prüfen
print('\n2) Beispiel-CSV Dateien in upload_beispiel_dateien prüfen')
if not os.path.isdir(EXAMPLE_DIR):
    print(f'   -> FEHLER: Beispielverzeichnis {EXAMPLE_DIR} nicht gefunden')
else:
    files = os.listdir(EXAMPLE_DIR)
    print('   -> Gefundene Dateien:', files)

    # profile.csv
    profile_path = os.path.join(EXAMPLE_DIR, 'profile.csv')
    if os.path.exists(profile_path):
        df = check_csv(profile_path)
        print('\n   profile.csv Spalten:', df.columns.tolist())
        req = [COLUMN_PROFILE_ID, 'Name']
        missing = [c for c in req if c not in df.columns]
        if missing:
            print('   -> Fehlende Spalten in profile.csv:', missing)
        else:
            print('   -> profile.csv OK')
    else:
        print('   -> profile.csv nicht gefunden')

    # antworten.csv
    answers_path = os.path.join(EXAMPLE_DIR, 'antworten.csv')
    if os.path.exists(answers_path):
        df = check_csv(answers_path)
        print('\n   antworten.csv Spalten:', df.columns.tolist())
        req = [COLUMN_INDEX, COLUMN_TIMESTAMP, COLUMN_PROFILE_ID]
        # also check role and cluster columns
        req += [COLUMN_ROLE]
        req += CLUSTER_COLUMNS
        missing = [c for c in req if c not in df.columns]
        if missing:
            print('   -> Fehlende erwartete Spalten in antworten.csv:', missing)
        else:
            print('   -> antworten.csv OK')
    else:
        print('   -> antworten.csv nicht gefunden')

    # rollen.csv
    rollen_path = os.path.join(EXAMPLE_DIR, 'rollen.csv')
    if os.path.exists(rollen_path):
        df = check_csv(rollen_path)
        print('\n   rollen.csv Spalten:', df.columns.tolist())
        req = [COLUMN_INDEX, COLUMN_ROLE]
        req += CLUSTER_COLUMNS
        missing = [c for c in req if c not in df.columns]
        if missing:
            print('   -> Fehlende erwartete Spalten in rollen.csv:', missing)
        else:
            print('   -> rollen.csv OK')
    else:
        print('   -> rollen.csv nicht gefunden')

    # fragebogen (Beispiel: Fragebogen.csv)
    fragebogen_path = os.path.join(EXAMPLE_DIR, 'Fragebogen.csv')
    if os.path.exists(fragebogen_path):
        df = check_csv(fragebogen_path)
        print('\n   Fragebogen.csv Spalten:', df.columns.tolist())
        req = [COLUMN_QUESTION_ID, COLUMN_CLUSTER_NUMBER, COLUMN_CLUSTER_NAME, COLUMN_SUBSCALE, COLUMN_QUESTION, COLUMN_INVERTED]
        missing = [c for c in req if c not in df.columns]
        if missing:
            print('   -> Fehlende erwartete Spalten in Fragebogen.csv:', missing)
        else:
            print('   -> Fragebogen.csv OK')
    else:
        print('   -> Fragebogen.csv nicht gefunden')

print('\n=== Prüfung abgeschlossen ===\n')
