import streamlit as st
import datetime as dt
from generate_random_data import generate_random_row, save_row_to_csv, DEMOGRAPHY_IDS
from functions.data import get_cluster_numbers, get_question_ids
import pandas as pd
import os
from functions.menu import default_menu

st.set_page_config(page_title="Datengenerierung", layout="wide")

default_menu()

st.title("Datengenerierung für Fragebogen-Datensätze")

# Index bestimmen (fortlaufend)
def get_next_index():
    path = 'generated_data.csv'
    if not os.path.exists(path):
        return 0
    try:
        df = pd.read_csv(path, sep=';')
        if 'index' in df.columns:
            return int(df['index'].max()) + 1
        else:
            return len(df)
    except Exception:
        return 0

# Eingabefelder
index = get_next_index()
speicherzeitpunkt = st.text_input("Speicherzeitpunkt", value=dt.datetime.now().strftime('%Y-%m-%d %H:%M'))
profil_id = st.text_input("Profil-ID", value="101")

st.header("Demographische Angaben")
demography_dict = {}
demography_dict["0SD01"] = st.radio(
    label="Branche",
    options=[
        "Industrie / Produktion",
        "Handwerk",
        "Handel",
        "IT / Software / Digitalisierung",
        "Gesundheitswesen / Soziale Dienste",
        "Bildung / Wissenschaft / Forschung",
        "Bauwesen / Architektur",
        "Energie / Umwelt",
        "Logistik / Transport",
        "Öffentlicher Dienst / Verwaltung",
        "Dienstleistung allgemein",
        "Sonstige"
    ],
    key="0SD01"
)
demography_dict["0SD01B"] = st.text_input("Branche (Wenn Sonstige)", key="0SD01B")
demography_dict["0SD02"] = st.text_input("In welcher Abteilung oder in welchem Bereich sind Sie zurzeit tätig?", key="0SD02")
demography_dict["0SD03"] = st.number_input("Wie lange gehören Sie bereits Ihrem aktuellen Team an? (Bitte geben Sie die Anzahl der Jahre an.)", min_value=0.0, max_value=99.0, step=0.5, key="0SD03")
demography_dict["0SD04"] = st.number_input("Wie lange arbeiten Sie bereits in Ihrem aktuellen Unternehmen?", min_value=0.0, max_value=99.0, step=0.5, key="0SD04")
demography_dict["0SD05"] = st.checkbox("Haben Sie derzeit Personalverantwortung? (ankreuzen falls ja)", key="0SD05", value=False)
demography_dict["0SD06"] = st.number_input("Wie alt sind Sie? (1 eingeben falls Sie nicht antworten möchten)", min_value=1, max_value=99, key="0SD06")

st.header("Cluster-Zielwerte und Abweichung")
cluster_numbers = get_cluster_numbers()
cluster_targets = {}
def_cluster = 3.0
for cluster in cluster_numbers:
    cluster_targets[str(cluster)] = st.number_input(f"Zielwert für Cluster {cluster}", min_value=1.0, max_value=5.0, value=def_cluster, step=0.1, format="%.1f")
abweichung = st.number_input("Globale Abweichung für alle Cluster", min_value=0.0, max_value=3.0, value=0.2, step=0.1, format="%.1f")

if st.button("Zufallsdatensatz generieren und speichern"):
    row = generate_random_row(index, speicherzeitpunkt, profil_id, demography_dict, cluster_targets, abweichung)
    save_row_to_csv(row)
    st.success("Datensatz wurde generiert und gespeichert!")

# Vorschau auf die letzten 5 generierten Datensätze
if os.path.exists('generated_data.csv'):
    st.subheader("Vorschau auf die letzten 5 generierten Datensätze:")
    df = pd.read_csv('generated_data.csv', sep=';')
    st.dataframe(df.tail(5))
