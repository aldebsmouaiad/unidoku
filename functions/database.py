import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from urllib.error import HTTPError, URLError

def connect_to_gsheet():
    """
    Verbindet mit der Google Tabelle.
    """
    return st.connection("gsheets", type=GSheetsConnection, ttl=0)

@st.cache_data(show_spinner=True, ttl=1800)
def get_dataframe_from_gsheet(worksheet_name, index_col = None, refresh_time_in_minutes = 30):
    """
    Lädt einen DataFrame aus der Google Tabelle und setzt optional eine Spalte als Index.
    
    Args:
        worksheet_name (str): Der Name des Arbeitsblatts.
        index_col (int oder str, optional): Die Spalte, die als Index gesetzt werden soll. Standard ist 0 (erste Spalte).
        refresh_time_in_minutes (int, optional): Die Zeit in Minuten, nach der die Daten aktualisiert werden sollen. Standard ist 30 Minuten.
    Returns:
        pd.DataFrame: Ein DataFrame, der die Daten aus dem angegebenen Arbeitsblatt enthält.
    """
    conn = connect_to_gsheet()
    try:
        import_dataframe = conn.read(worksheet=worksheet_name, ttl=refresh_time_in_minutes)
    except HTTPError as e:
        # Häufige Ursache: fehlende Berechtigungen oder falsche Spreadsheet-URL
        raise RuntimeError(
            f"HTTP error beim Lesen des Worksheets '{worksheet_name}': {e.code} {e.reason}.\n"
            "Prüfe: 1) Ist die Spreadsheet-URL in '.streamlit/secrets.toml' korrekt?\n"
            "2) Wurde die Spreadsheet-Datei mit dem in den Secrets angegebenen Service Account (client_email) geteilt?\n"
            "3) Existiert ein Worksheet/Tab mit exakt diesem Namen (Groß-/Kleinschreibung beachten)?"
        ) from e
    except URLError as e:
        raise RuntimeError(
            f"Netzwerk/URL error beim Lesen des Worksheets '{worksheet_name}': {e.reason}.\n"
            "Prüfe die Erreichbarkeit der Google Sheets URL und deine Netzwerkverbindung"
        ) from e
    except Exception as e:
        # Allgemeine Fehlermeldung mit Hinweis, wo nachzusehen ist
        raise RuntimeError(
            f"Fehler beim Laden des Worksheets '{worksheet_name}': {e}\n"
            "Überprüfe die Spreadsheet-URL, die Freigaben für den Service Account (client_email in .streamlit/secrets.toml)",
        ) from e
    if index_col is not None:
        import_dataframe = import_dataframe.set_index(index_col)
    return import_dataframe

def update_dataframe_to_gsheet(worksheet_name, dataframe):
    """
    Lädt einen DataFrame in die Google Tabelle.
    Args:
        worksheet_name (str): Der Name des Arbeitsblatts.
        dataframe (pd.DataFrame): Der DataFrame, der in die Google Tabelle geladen werden soll.
    """
    conn = connect_to_gsheet()
    dataframe_without_index = dataframe.reset_index()
    conn.update(worksheet=worksheet_name, data=dataframe_without_index)
    st.cache_data.clear()
