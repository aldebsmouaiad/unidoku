import streamlit as st
import pandas as pd
from config import GOOGLE_SHEET_PROFILES, COLUMN_PROFILE_ID
from functions.database import get_dataframe_from_gsheet, update_dataframe_to_gsheet

def create_profile(id, name, role=None):
    # Funktion zur Erstellung eines neuen Profils.
    data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)
    data_profiles.loc[id, "Name"] = name
    if role:
        data_profiles.loc[id, "Rollen-Name"] = role
    update_dataframe_to_gsheet(GOOGLE_SHEET_PROFILES, data_profiles)
