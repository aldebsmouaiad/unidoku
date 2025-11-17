import pandas as pd
import numpy as np
import datetime as dt
from functions.data import get_question_ids
from config import PATH_QUESTIONNAIRE

# Konfiguration
CSV_PATH = 'generated_data.csv'

DEMOGRAPHY_IDS = [
    "0SD01", "0SD01B", "0SD02", "0SD03", "0SD04", "0SD05", "0SD06"
]

# Hilfsfunktion: Cluster-zu-Fragen-Zuordnung
def get_cluster_to_questions():
    fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=';', encoding='utf-8')
    cluster_map = {}
    for cluster in fragebogen['Cluster-Nummer'].unique():
        cluster_map[str(cluster)] = fragebogen[fragebogen['Cluster-Nummer'] == cluster]['Frage-ID'].tolist()
    return cluster_map

# Zufallsantworten für einen Cluster generieren
# Ziel: Durchschnitt im Intervall [zielwert - abweichung, zielwert + abweichung]
def generate_cluster_answers(num_questions, zielwert, abweichung):
    # Erlaubter Bereich für den Durchschnitt
    min_avg = max(1, zielwert - abweichung)
    max_avg = min(5, zielwert + abweichung)
    # Versuche, bis ein passender Satz gefunden wurde
    for _ in range(1000):
        werte = np.random.randint(1, 6, size=num_questions)
        avg = np.mean(werte)
        if min_avg <= avg <= max_avg:
            return werte.tolist()
    # Fallback: Nimm den Zielwert gerundet
    return [int(round(zielwert))] * num_questions

# Hauptfunktion zur Generierung einer Zeile
def generate_random_row(index, speicherzeitpunkt, profil_id, demography_dict, cluster_targets, abweichung):
    """
    Generiert eine zufällige Zeile für den Fragebogen.
    """
    question_ids = get_question_ids()
    cluster_map = get_cluster_to_questions()
    # Antworten für alle Fragen generieren
    answers = {}
    for cluster_num, zielwert in cluster_targets.items():
        fragen = cluster_map[str(cluster_num)]
        werte = generate_cluster_answers(len(fragen), zielwert, abweichung)
        for qid, val in zip(fragen, werte):
            answers[qid] = val
    # Demographie ergänzen
    for demoid in DEMOGRAPHY_IDS:
        answers[demoid] = demography_dict.get(demoid, "")
    # Reihenfolge: index, Speicherzeitpunkt, alle Frage-IDs, dann Demographie
    row = {
        'index': index,
        'Speicherzeitpunkt': speicherzeitpunkt,
        'Profil-ID': profil_id
    }
    for qid in question_ids:
        row[qid] = answers.get(qid, "")
    for demoid in DEMOGRAPHY_IDS:
        row[demoid] = answers.get(demoid, "")
    return row


def save_row_to_csv(row, path=CSV_PATH):
    """
    Speichert eine Zeile in die CSV-Datei.
    """
    try:
        df = pd.read_csv(path, sep=';', index_col=False)
    except FileNotFoundError:
        df = pd.DataFrame()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, sep=';', index=False)
