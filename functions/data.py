import pandas as pd
import streamlit as st

from config import (
    PATH_QUESTIONNAIRE,
    GOOGLE_SHEET_ANSWERS,
    COLUMN_INDEX,
    GOOGLE_SHEET_BEDARFE,
    COLUMN_TIMESTAMP,
    COLUMN_PROFILE_ID,
    COLUMN_ROLE,
    COLUMN_QUESTION_ID,
    COLUMN_CLUSTER_NAME,
    COLUMN_SUBSCALE,
    COLUMN_INVERTED,
    COLUMN_CLUSTER_NUMBER,
)
from functions.database import get_dataframe_from_gsheet


def get_amount_questions():
    """
    Ruft die Anzahl der Fragen im Fragebogen ab.

    Returns:
        int: Anzahl der Fragen im Fragebogen
    """

    if not st.session_state.import_mode:
        fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=";", encoding="utf-8")
    else:
        fragebogen = st.session_state["uploaded_data"]["fragebogen"]
    return fragebogen.shape[0]


def invert_corresponding_answers(df):
    """
    Invertiert die Antworten, die im Fragebogen als invertiert markiert sind.

    Args:
        df (pandas.DataFrame): DataFrame mit den Antworten

    Returns:
        pandas.DataFrame: DataFrame mit invertierten Antworten für entsprechend markierte Fragen
    """
    # Funktion zum invertieren der im Fragebogen entsprechend markierten Antworten.
    invert_dict = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}
    if not st.session_state.import_mode:
        fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=";", encoding="utf-8")
    else:
        fragebogen = st.session_state["uploaded_data"]["fragebogen"]

    df_with_inverted_answers = df
    for index in df_with_inverted_answers.index:
        if (
            index in fragebogen[COLUMN_QUESTION_ID].values
            and fragebogen.loc[fragebogen[COLUMN_QUESTION_ID] == index, COLUMN_INVERTED].values[0]
            is True
        ):
            df_with_inverted_answers.loc[index] = invert_dict[
                df_with_inverted_answers.loc[index]
            ]
    return df_with_inverted_answers


def calculate_cluster_values(df):
    """
    Berechnet die Cluster-Werte für die gegebenen Antworten.

    Args:
        df (pandas.DataFrame): DataFrame mit den Antworten

    Returns:
        list: Liste der berechneten Cluster-Werte
    """
    df_with_inverted_answers = invert_corresponding_answers(df)
    cluster_values = []
    for i in range(len(get_cluster_names())):
        mask = df_with_inverted_answers.index.str.match(rf"^{i + 1}[A-Z]")
        cluster_answers = df_with_inverted_answers[mask]
        cluster_value = round(cluster_answers.sum() / len(cluster_answers), 1)
        cluster_values.append(cluster_value)
    return cluster_values


def get_cluster_names():
    """
    Ruft die Namen der Cluster aus dem Fragebogen ab.

    Returns:
        numpy.ndarray: Array mit den eindeutigen Cluster-Namen
    """
    # Funktion zum Abrufen der Cluster-Namen des hinterlegten Fragebogens.
    if not st.session_state.import_mode:
        fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=";", encoding="utf-8")
    else:
        fragebogen = st.session_state["uploaded_data"]["fragebogen"]
    return fragebogen[COLUMN_CLUSTER_NAME].unique()


def get_questionnaire_summary():
    """
    Erstellt eine Zusammenfassung des Fragebogens mit Details zu Subskalen und Clustern.
    Returns:
        dict: Dictionary
    """
    # Fragebogen einlesen
    if not st.session_state.import_mode:

        fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=";", encoding="utf-8")
    else:
        fragebogen = st.session_state["uploaded_data"]["fragebogen"]
    
    fragebogen = fragebogen[fragebogen[COLUMN_SUBSCALE] != "KONTROLLFRAGE"]

    summary_dict = {}

    # Gesamtanzahl Fragen pro Cluster vorberechnen
    cluster_counts = fragebogen.groupby(COLUMN_CLUSTER_NUMBER)[COLUMN_QUESTION_ID].count().to_dict()

    # Daten nach Subskala gruppieren
    for subscale, group in fragebogen.groupby(COLUMN_SUBSCALE):
        cluster_num = group[COLUMN_CLUSTER_NUMBER].iloc[0]
        cluster_name = group[COLUMN_CLUSTER_NAME].iloc[0]
        questions_in_subscale = group[COLUMN_QUESTION_ID].count()
        questions_in_cluster = cluster_counts[cluster_num]

        # Frage-IDs für diese Subskala extrahieren
        question_ids = group[COLUMN_QUESTION_ID].tolist()

        summary_dict[subscale] = {
            "Cluster-Nummer": int(cluster_num),
            "Cluster-Name": cluster_name,
            "Fragenanzahl_Subskala": int(questions_in_subscale),
            "Fragenanzahl_Cluster": questions_in_cluster,
            "Frage-IDs": question_ids,
        }

    return summary_dict


def get_cluster_numbers():
    """
    Ruft die Nummern der Cluster aus dem Fragebogen ab.

    Returns:
        numpy.ndarray: Array mit den eindeutigen Cluster-Nummern
    """
    # Funktion zum Abrufen der Cluster-Nummern des hinterlegten Fragebogens.
    fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=";", encoding="utf-8")
    return fragebogen[COLUMN_CLUSTER_NUMBER].unique()


def get_cluster_table():
    """
    Erstellt eine Tabelle mit Cluster-Nummern und zugehörigen Namen.

    Returns:
        pandas.DataFrame: DataFrame mit Cluster-Nummern als Index und Cluster-Namen als Spalte
    """
    # Funktion zum Abrufen der Cluster-Nummern des hinterlegten Fragebogens.
    fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=";", encoding="utf-8")
    cluster_data = fragebogen[[COLUMN_CLUSTER_NUMBER, COLUMN_CLUSTER_NAME]].drop_duplicates()
    cluster_data.set_index("Cluster-Nummer", inplace=True)
    return cluster_data


def get_question_ids():
    """
    Ruft alle Frage-IDs aus dem Fragebogen als Liste ab.

    Returns:
        list: Liste aller Frage-IDs
    """
    # Funktion zum Abrufen der Frage-IDs als Liste.
    fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=";", encoding="utf-8")
    return fragebogen[COLUMN_QUESTION_ID].tolist()


def get_latest_update_time(profil_id):
    """
    Ruft den Zeitpunkt des letzten Eintrags für eine bestimmte Profil-ID ab.

    Args:
        profil_id: Profil-ID für die der letzte Eintrag gesucht wird

    Returns:
        str or None: Zeitpunkt des letzten Eintrags oder None falls keine Einträge vorhanden
    """
    # Funktion zum Abrufen des letzten Eintrags für die gegebene ID.
    if not st.session_state.import_mode:
        answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)
    else:
        answers = st.session_state["uploaded_data"][GOOGLE_SHEET_ANSWERS]
        answers = answers.set_index(COLUMN_INDEX)

    answers[COLUMN_TIMESTAMP] = pd.to_datetime(
        answers[COLUMN_TIMESTAMP], format="%d.%m.%Y %H:%M"
    )
    filtered_answers = answers[answers[COLUMN_PROFILE_ID] == profil_id]
    if len(filtered_answers) == 0:
        return None
    sorted_answers = filtered_answers.sort_values(by=COLUMN_TIMESTAMP, ascending=False)  # type: ignore
    return sorted_answers[COLUMN_TIMESTAMP].values[0]


def get_cluster_values_for_correlation_matrix(dataframe: pd.DataFrame):
    """
    Berechnet die Cluster-Werte aus dem Fragebogen.

    Args:
        dataframe (pandas.DataFrame): DataFrame mit allen Antworten

    Returns:
        dataframe (pandas.DataFrame): DataFrame mit den Cluster-Werten
    """
    df = dataframe.reset_index(drop=True)
    df = df.apply(calculate_cluster_values, axis=1)
    df = pd.DataFrame(df.tolist())
    cluster_names = get_cluster_names()
    df.columns = cluster_names
    return df


def get_selected_cluster_values(
    profil_id: str | int, timestamp: str
) -> list[float] | None:
    """
    Berechnet die Cluster-Werte aus dem aktuellsten Fragebogen für eine bestimmte Profil-ID.

    Args:
        profil_id: Profil-ID für die die Cluster-Werte berechnet werden sollen
        timestamp: Zeitpunkt für den die Cluster-Werte berechnet werden sollen

    Returns:
        list or None: Liste der Cluster-Werte oder None falls keine Antworten vorhanden
    """
    if not st.session_state.import_mode:
        answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)
    else:
        answers = st.session_state["uploaded_data"][GOOGLE_SHEET_ANSWERS]
        answers = answers.set_index(COLUMN_INDEX)

    answers[COLUMN_TIMESTAMP] = pd.to_datetime(
        answers[COLUMN_TIMESTAMP], format="%d.%m.%Y %H:%M"
    )

    # Filtere die Antworten nach Profil-ID und Zeitpunkt
    filtered_answers = answers[
        (answers[COLUMN_PROFILE_ID] == profil_id)
        & (answers[COLUMN_TIMESTAMP] == timestamp)
    ]

    if filtered_answers.empty:
        return None

    latest_answer = filtered_answers.iloc[0]

    try:
        return calculate_cluster_values(latest_answer)
    except Exception as e:
        print(f"Fehler bei der Cluster-Berechnung für Profil {profil_id}: {e}")
        return None


def get_cluster_values_over_time(profil_id, cluster_name):
    """
    Berechnet die Cluster-Werte für eine bestimmte Kategorie über die Zeit.

    Args:
        profil_id: Profil-ID für die die Cluster-Werte berechnet werden sollen
        cluster_name (str): Name der Kategorie/des Clusters

    Returns:
        pandas.DataFrame: DataFrame mit Zeitpunkten und Cluster-Werten für die gegebene Kategorie
    """
    # Alle Antworten für die Profil-ID laden
    if not st.session_state.import_mode:
        answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)
    else:
        answers = st.session_state["uploaded_data"][GOOGLE_SHEET_ANSWERS]
        answers = answers.set_index(COLUMN_INDEX)

    answers[COLUMN_TIMESTAMP] = pd.to_datetime(
        answers[COLUMN_TIMESTAMP], format="%d.%m.%Y %H:%M"
    )
    filtered_answers = answers[answers[COLUMN_PROFILE_ID] == profil_id]

    if len(filtered_answers) == 0:
        return pd.DataFrame()

    # Nach Zeitpunkt sortieren
    sorted_answers = filtered_answers.sort_values(by=COLUMN_TIMESTAMP, ascending=True)  # type: ignore

    # Cluster-Nummer für die gegebene Kategorie finden
    if not st.session_state.import_mode:
        fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=";", encoding="utf-8")
    else:
        fragebogen = st.session_state["uploaded_data"]["fragebogen"]
    cluster_data = fragebogen[fragebogen[COLUMN_CLUSTER_NAME] == cluster_name]
    cluster_number = int(cluster_data[COLUMN_CLUSTER_NUMBER].iloc[0])

    # Zeitpunkte und Cluster-Werte sammeln
    time_data = []
    cluster_values = []

    for _, row in sorted_answers.iterrows():
        # Cluster-Werte für diesen Zeitpunkt berechnen
        cluster_value = calculate_cluster_values(row)[
            cluster_number - 1
        ]  # -1 weil Index bei 0 beginnt
        time_data.append(row[COLUMN_TIMESTAMP])
        cluster_values.append(cluster_value)

    # DataFrame erstellen
    result_df = pd.DataFrame({"Zeitpunkt": time_data, "Wert": cluster_values})

    return result_df


def get_subscale_values_over_time(profil_id, subscale_name):
    """
    Berechnet die Subskala-Werte für eine bestimmte Subskala über die Zeit.

    Args:
        profil_id: Profil-ID für die die Subskala-Werte berechnet werden sollen
        subscale_name (str): Name der Subskala

    Returns:
        pandas.DataFrame: DataFrame mit Zeitpunkten und Subskala-Werten für die gegebene Subskala
    """
    # Alle Antworten für die Profil-ID laden
    if not st.session_state.import_mode:
        answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_INDEX)
    else:
        answers = st.session_state["uploaded_data"][GOOGLE_SHEET_ANSWERS]
        answers = answers.set_index(COLUMN_INDEX)

    answers[COLUMN_TIMESTAMP] = pd.to_datetime(
        answers[COLUMN_TIMESTAMP], format="%d.%m.%Y %H:%M"
    )
    filtered_answers = answers[answers[COLUMN_PROFILE_ID] == profil_id]

    if len(filtered_answers) == 0:
        return pd.DataFrame()

    # Nach Zeitpunkt sortieren
    sorted_answers = filtered_answers.sort_values(by=COLUMN_TIMESTAMP, ascending=True)  # type: ignore

    # Fragebogen laden und Frage-IDs für die Subskala finden
    if not st.session_state.import_mode:
        fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=";", encoding="utf-8")
    else:
        fragebogen = st.session_state["uploaded_data"]["fragebogen"]

    subscale_data = fragebogen[fragebogen[COLUMN_SUBSCALE] == subscale_name]
    question_ids = subscale_data[COLUMN_QUESTION_ID].tolist()

    if not question_ids:
        return pd.DataFrame()

    # Zeitpunkte und Subskala-Werte sammeln
    time_data = []
    subscale_values = []

    for _, row in sorted_answers.iterrows():
        # Nur die Fragen für diese Subskala betrachten
        subscale_answers = row[question_ids]

        # Invertierte Antworten berücksichtigen
        df_with_inverted_answers = invert_corresponding_answers(subscale_answers)

        # Durchschnittswert für die Subskala berechnen
        subscale_value = round(
            df_with_inverted_answers.sum() / len(df_with_inverted_answers), 1
        )

        time_data.append(row[COLUMN_TIMESTAMP])
        subscale_values.append(subscale_value)

    # DataFrame erstellen
    result_df = pd.DataFrame({"Zeitpunkt": time_data, "Wert": subscale_values})

    return result_df


def get_bedarfe_for_role(role: str | int, timestamp: str) -> list[float] | None:
    """
    Ruft die Bedarfe für eine bestimmte Rolle ab.

    Args:
        role: Rollen ID für die die Bedarfe abgerufen werden sollen
        timestamp: Zeitpunkt für den die Bedarfe abgerufen werden sollen

    Returns:
        list or None: Liste der Bedarfe für alle 11 Cluster oder None falls nicht gefunden
    """
    if not st.session_state.import_mode:
        bedarfe_df = get_dataframe_from_gsheet(GOOGLE_SHEET_BEDARFE, index_col=COLUMN_INDEX)
    else:
        bedarfe_df = st.session_state["uploaded_data"][GOOGLE_SHEET_BEDARFE]
        bedarfe_df = bedarfe_df.set_index(COLUMN_INDEX)

    bedarfe_df[COLUMN_TIMESTAMP] = pd.to_datetime(
        bedarfe_df[COLUMN_TIMESTAMP], format="%d.%m.%Y %H:%M"
    )

    # Filtere nach Rolle und Zeitpunkt
    filtered_bedarf = bedarfe_df[
        (bedarfe_df[COLUMN_ROLE] == role) & (bedarfe_df[COLUMN_TIMESTAMP] == timestamp)
    ]

    if filtered_bedarf.empty:
        return None

    latest_bedarf = filtered_bedarf.iloc[0]

    # Extrahiere die Cluster-Bedarfe
    cluster_anzahl = len(get_cluster_names()) + 1
    cluster_bedarfe = []
    for i in range(1, cluster_anzahl):
        cluster_bedarfe.append(latest_bedarf[f"cluster{i}"])

    return cluster_bedarfe


def get_latest_update_time_bedarf(role):
    """
    Ruft den Zeitpunkt des letzten Eintrags für eine bestimmte Rolle ab.

    Args:
        role: Rolle für die der letzte Eintrag gesucht wird

    Returns:
        str or None: Zeitpunkt des letzten Eintrags oder None falls keine Einträge vorhanden
    """
    # Funktion zum Abrufen des letzten Eintrags für die gegebene ID.
    if not st.session_state.import_mode:
        bedarfe = get_dataframe_from_gsheet(GOOGLE_SHEET_BEDARFE, index_col=COLUMN_INDEX)
    else:
        bedarfe = st.session_state["uploaded_data"][GOOGLE_SHEET_BEDARFE]
        bedarfe = bedarfe.set_index(COLUMN_INDEX)

    bedarfe[COLUMN_TIMESTAMP] = pd.to_datetime(
        bedarfe[COLUMN_TIMESTAMP], format="%d.%m.%Y %H:%M"
    )
    filtered_bedarfe = bedarfe[bedarfe[COLUMN_ROLE] == role]
    if len(filtered_bedarfe) == 0:
        return None
    sorted_bedarfe = filtered_bedarfe.sort_values(by=COLUMN_TIMESTAMP, ascending=False)  # type: ignore
    return sorted_bedarfe[COLUMN_TIMESTAMP].values[0]


def calculate_cluster_differences(
    actual_profile_id, bedarfe_profile_id, profil_timestamp, bedarfe_timestamp
):
    """
    Berechnet die Differenzen zwischen tatsächlichen Cluster-Werten und Bedarfen.

    Args:
        actual_profile_id: Profil-ID für die Profil Werte
        bedarfe_profile_id: Profil-ID für die Bedarfe
        profil_timestamp: Speicherzeitpunkt der Profil Werte
        bedarfe_timestamp: Speicherzeitpunkt der Bedarfe

    Returns:
        pandas.DataFrame: DataFrame mit Cluster-Namen und Differenzen
    """
    # Aktuelle Cluster-Werte laden
    actual_values = get_selected_cluster_values(actual_profile_id, profil_timestamp)
    if actual_values is None:
        return pd.DataFrame()

    # Bedarfe laden
    bedarfe_values = get_bedarfe_for_role(bedarfe_profile_id, bedarfe_timestamp)
    if bedarfe_values is None:
        return pd.DataFrame()

    # Cluster-Namen laden
    cluster_names = get_cluster_names()

    # Differenzen berechnen (Ist - Bedarf)
    differences = []
    for i in range(len(cluster_names)):
        diff = actual_values[i] - bedarfe_values[i]
        differences.append(diff)

    # DataFrame erstellen
    result_df = pd.DataFrame({"Cluster": cluster_names, "Differenz": differences})

    # Nach Differenz sortieren (größte negative zuerst)
    result_df = result_df.sort_values("Differenz", ascending=True)

    return result_df


def calculate_time_differences(profile_id, first_timestamp, second_timestamp):
    """
    Berechnet die Differenzen zwischen zwei Zeitpunkten für dasselbe Profil.

    Args:
        profile_id: Profil-ID für die die Differenzen berechnet werden sollen
        first_timestamp: Erster Zeitpunkt
        second_timestamp: Zweiter Zeitpunkt

    Returns:
        pandas.DataFrame: DataFrame mit Cluster-Namen und Differenzen
    """
    # Werte für beide Zeitpunkte laden
    first_values = get_selected_cluster_values(profile_id, first_timestamp)
    second_values = get_selected_cluster_values(profile_id, second_timestamp)
    cluster_names = get_cluster_names()

    # Prüfen ob Werte verfügbar sind
    if first_values is None or second_values is None or cluster_names is None:
        return pd.DataFrame()

    # Differenzen berechnen (Zweiter Zeitpunkt - Erster Zeitpunkt)
    differences = [second - first for second, first in zip(second_values, first_values)]

    # DataFrame für das Diagramm erstellen
    result_df = pd.DataFrame({"Cluster": cluster_names, "Differenz": differences})

    # Nach Differenz sortieren (größte negative zuerst)
    result_df = result_df.sort_values("Differenz", ascending=True)

    return result_df


def calculate_time_differences_bedarfe(
    data_bedarfe, role, first_timestamp, second_timestamp
):
    """
    Berechnet die Differenzen zwischen zwei Zeitpunkten für dasselbe Bedarfs-Profil.
    Die Werte werden direkt aus der Bedarfe-Tabelle genommen.

    Args:
        data_bedarfe (pandas.DataFrame): DataFrame mit Bedarfs-Daten
        role: Rolle für die die Bedarfe abgerufen werden sollen
        first_timestamp: Erster Zeitpunkt
        second_timestamp: Zweiter Zeitpunkt

    Returns:
        pandas.DataFrame: DataFrame mit Cluster-Namen und Differenzen
    """
    bedarfe_df = data_bedarfe
    # Werte für beide Zeitpunkte und Profil-ID filtern
    first_row = bedarfe_df[
        (bedarfe_df[COLUMN_ROLE] == role)
        & (bedarfe_df[COLUMN_TIMESTAMP] == first_timestamp)
    ]
    second_row = bedarfe_df[
        (bedarfe_df[COLUMN_ROLE] == role)
        & (bedarfe_df[COLUMN_TIMESTAMP] == second_timestamp)
    ]
    cluster_names = get_cluster_names()

    if first_row.empty or second_row.empty or cluster_names is None:
        return pd.DataFrame()

    # Werte extrahieren
    first_values = [
        float(first_row.iloc[0][f"cluster{i}"])
        for i in range(1, len(cluster_names) + 1)
    ]
    second_values = [
        float(second_row.iloc[0][f"cluster{i}"])
        for i in range(1, len(cluster_names) + 1)
    ]

    # Differenzen berechnen (Zweiter Zeitpunkt - Erster Zeitpunkt)
    differences = [second - first for second, first in zip(second_values, first_values)]

    # DataFrame für das Diagramm erstellen
    result_df = pd.DataFrame({"Cluster": cluster_names, "Differenz": differences})

    # Nach Differenz sortieren (größte negative zuerst)
    result_df = result_df.sort_values("Differenz", ascending=True)

    return result_df


def calculate_development_gap(ist_differences_df, bedarf_differences_df):
    """
    Berechnet die Differenz zwischen Profil-Entwicklung und Bedarf-Entwicklung.

    Args:
        ist_differences_df (pandas.DataFrame): DataFrame mit Profil-Entwicklungsdifferenzen
        bedarf_differences_df (pandas.DataFrame): DataFrame mit Bedarf-Entwicklungsdifferenzen

    Returns:
        pandas.DataFrame: DataFrame mit Cluster-Namen und Differenzen (Profil-Entwicklung - Bedarf-Entwicklung)
    """
    if ist_differences_df.empty or bedarf_differences_df.empty:
        return pd.DataFrame()

    # DataFrames nach Cluster sortieren, um sicherzustellen, dass sie übereinstimmen
    ist_sorted = ist_differences_df.sort_values("Cluster").reset_index(drop=True)
    bedarf_sorted = bedarf_differences_df.sort_values("Cluster").reset_index(drop=True)

    # Differenzen berechnen (Profil-Entwicklung - Bedarf-Entwicklung)
    development_gaps = ist_sorted["Differenz"] - bedarf_sorted["Differenz"]

    # DataFrame erstellen
    result_df = pd.DataFrame(
        {"Cluster": ist_sorted["Cluster"], "Differenz": development_gaps}
    )

    # Nach Differenz sortieren (größte negative zuerst)
    result_df = result_df.sort_values("Differenz", ascending=True)

    return result_df


def create_gap_analysis_chart(
    differences_df,
    title,
    xaxis_title,
    show_legend=False,
    title_font_size=None,
    bar_color=None,
    negative_color=None,
    positive_color=None,
):
    """
    Erstellt ein horizontales Balkendiagramm für Gap-Analysen.

    Args:
        differences_df (pandas.DataFrame): DataFrame mit 'Cluster' und 'Differenz' Spalten
        title (str): Titel des Diagramms
        xaxis_title (str): Titel der X-Achse
        show_legend (bool): Ob die Legende angezeigt werden soll
        title_font_size (int, optional): Schriftgröße für den Titel
        bar_color (str, optional): Einzelfarbe für alle Balken (z. B. 'blue')
        negative_color (str, optional): Farbe für negative Abweichungen (Standard 'red')
        positive_color (str, optional): Farbe für positive Abweichungen (Standard 'blue')

    Returns:
        plotly.graph_objects.Figure: Das erstellte Diagramm
    """
    import plotly.graph_objects as go

    if differences_df.empty:
        return None

    # Farben bestimmen: Einzel-Farbe, oder pos/neg Mapping, Standard bleibt rot/grün
    if bar_color is not None:
        marker_color = bar_color
    else:
        neg_col = negative_color if negative_color is not None else "red"
        pos_col = positive_color if positive_color is not None else "blue"
        marker_color = [
            neg_col if x < 0 else pos_col for x in differences_df["Differenz"]
        ]

    # Horizontales Barchart erstellen
    fig = go.Figure()

    # Balken hinzufügen
    fig.add_trace(
        go.Bar(
            y=differences_df["Cluster"],
            x=differences_df["Differenz"],
            orientation="h",
            marker_color=marker_color,
            text=[f"{x:.1f}" for x in differences_df["Differenz"]],
            textposition="auto",
            textangle=0,
            name="Differenz",
        )
    )

    # Zweiten Balken hinzufügen
    if differences_df.shape[1] > 2:
        fig.add_trace(
            go.Bar(
                y=differences_df["Cluster"],
                x=differences_df["Ist-Werte"],
                orientation="h",
                marker_color="grey",
                text=[f"{x:.1f}" for x in differences_df["Differenz"]],
                textposition="auto",
                textangle=0,
                name="Differenz",
            )
        )

    # Layout anpassen
    layout_dict = {
        "title": title,
        "xaxis_title": xaxis_title,
        "yaxis_title": "Cluster",
        "xaxis": dict(
            zeroline=True,
            zerolinecolor="black",
            zerolinewidth=2,
            range=[
                differences_df["Differenz"].min() - 0.5,
                differences_df["Differenz"].max() + 0.5,
            ],
        ),
        "yaxis": dict(autorange="reversed"),  # Größte negative Abweichung oben
        "height": 400,
        "showlegend": show_legend,
    }

    # Schriftgröße für Titel hinzufügen, falls angegeben
    if title_font_size is not None:
        layout_dict["title_font_size"] = title_font_size

    fig.update_layout(**layout_dict)

    # Hinzufügen einer vertikalen Linie bei 0
    fig.add_vline(x=0, line_width=2, line_color="black", line_dash="solid")

    return fig


def get_gap_analysis_legend(analysis_type="analyse"):
    """
    Gibt die passende Legende für Gap-Analysen zurück.

    Args:
        analysis_type (str): Art der Analyse ("analyse", "zeitvergleich" oder "entwicklung_gap")

    Returns:
        str: Markdown-formatierte Legende
    """
    if analysis_type == "analyse":
        return """
        **Legende:**
        - 🔴 **Rot**: Negative Abweichung (Profil < Bedarf) - Verbesserungspotential
        - 🔵 **Blau**: Positive Abweichung (Profil > Bedarf) - Stärke
        """
    elif analysis_type == "zeitvergleich":
        return """
        **Legende:**
        - 🔴 **Rot**: Verschlechterung (Später < Früher)
        - 🔵 **Blau**: Verbesserung (Später > Früher)
        """
    elif analysis_type == "entwicklung_gap":
        return """
        **Legende:**
        - 🔴 **Rot**: Negative Abweichung (Profil-Entwicklung < Bedarf-Entwicklung)
        - 🔵 **Blau**: Positive Abweichung (Profil-Entwicklung > Bedarf-Entwicklung)
        - ⚫ **Grau**: Aktuelle Abweichung (zum zweiten Zeitpunkt)
        """
    else:
        return ""


