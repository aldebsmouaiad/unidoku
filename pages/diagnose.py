import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from functions.menu import default_menu, admin_check
from functions.page import footer
from config import (
    GOOGLE_SHEET_PROFILES,
    COLUMN_PROFILE_ID,
    GOOGLE_SHEET_ANSWERS,
    COLUMN_TIMESTAMP,
    GOOGLE_SHEET_BEDARFE,
    COLUMN_ROLE,
)
from functions.database import get_dataframe_from_gsheet
from functions.data import (
    calculate_time_differences,
    create_gap_analysis_chart,
    get_gap_analysis_legend,
    calculate_time_differences_bedarfe,
    get_cluster_values_for_correlation_matrix,
    calculate_development_gap,
    calculate_cluster_differences
)
from functions.session_state import check_mode, require_uploaded_data

# -Seitenkonfiguration-
st.set_page_config(page_title="Diagnose", layout="wide")
check_mode()
admin_check()
default_menu()

# Konfiguration für Schriftgrößen der Diagrammtitel
TITLE_FONT_SIZE_INCREASE = 10

st.title("Diagnose")

# -Daten laden-
if not st.session_state.import_mode:
    data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)
    data_answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS, index_col=COLUMN_TIMESTAMP)
    data_bedarfe = get_dataframe_from_gsheet(GOOGLE_SHEET_BEDARFE, index_col=COLUMN_TIMESTAMP)

else:
    # Prüfen, ob alle erforderlichen Upload-Daten vorhanden sind
    required_keys = {GOOGLE_SHEET_PROFILES, GOOGLE_SHEET_ANSWERS, GOOGLE_SHEET_BEDARFE, "fragebogen"}
    require_uploaded_data(required_keys)

    # Daten aus Upload laden
    data_profiles = st.session_state["uploaded_data"][GOOGLE_SHEET_PROFILES].set_index(COLUMN_PROFILE_ID)
    data_answers = st.session_state["uploaded_data"][GOOGLE_SHEET_ANSWERS].set_index(COLUMN_TIMESTAMP)
    data_bedarfe = st.session_state["uploaded_data"][GOOGLE_SHEET_BEDARFE].set_index(COLUMN_TIMESTAMP)

data_answers.index = pd.to_datetime(data_answers.index, format='%d.%m.%Y %H:%M')
data_bedarfe.index = pd.to_datetime(data_bedarfe.index, format='%d.%m.%Y %H:%M')

data_answers_real = pd.read_csv("data/antworten_real.csv", sep=',', encoding='utf-8')


col1, col2 = st.columns(2)

with col1:
    # Profil auswählen
    st.subheader("Auswahl Profil")
    set_name_active_profile = st.selectbox(
        "Profil auswählen:", data_profiles[["Name"]], key="profil_auswahl_1"
    )
    set_id_active_profile = data_profiles.index[
        data_profiles["Name"] == set_name_active_profile
    ][0]

    # Zeitpunkt auswählen
    filtered_update_time = data_answers.index[
        data_answers[COLUMN_PROFILE_ID] == set_id_active_profile
    ]

    # Falls keine Zeitpunkte vorhanden sind, abbrechen mit Hinweis
    if len(filtered_update_time) == 0:
        st.warning("Für dieses Profil sind noch keine Zeitpunkte/Antworten vorhanden. Bitte füllen Sie den Fragebogen aus.")
        st.stop()

    set_first_timestamp_active_profile, set_second_timestamp_active_profile = st.select_slider(
        label = "Zeitpunkte für den Vergleich auswählen:",
        options = filtered_update_time,
        value = [max(filtered_update_time), min(filtered_update_time)],
        format_func=lambda x: x.strftime("%d.%m.%Y") if hasattr(x, "strftime") else str(x)
    )

    # Prüfen und Rolle ausgeben
    if set_id_active_profile in data_answers[COLUMN_PROFILE_ID].values:
        role_for_selection = data_answers.loc[(data_answers.index == set_second_timestamp_active_profile) & (data_answers[COLUMN_PROFILE_ID] == set_id_active_profile), COLUMN_ROLE].values[0]
    else:
        st.warning("Für dieses Profil sind noch keine Antworten vorhanden. Bitte füllen Sie den Fragebogen aus.")
        st.stop()
    if pd.isna(role_for_selection):
        role_for_selection = "Keine Rolle zugewiesen"
    st.write(f"Rolle zum gewählten Zeitpunkt: {role_for_selection}")


with col2:
    st.subheader("Auswahl Rolle")

    unique_bedarf_roles = data_bedarfe[COLUMN_ROLE].dropna().unique().tolist()

    # Rolle zum ausgewählten Zeitpunkt ermitteln
    default_role_index = None
    if len(filtered_update_time) > 0 and COLUMN_ROLE in data_answers.columns:
        try:
            # Verwende den letzten Zeitpunkt als Standard
            selected_timestamp = filtered_update_time[-1]
            role_mask = (data_answers.index == selected_timestamp) & (data_answers[COLUMN_PROFILE_ID] == set_id_active_profile)
            role_rows = data_answers.loc[role_mask, COLUMN_ROLE]
            if len(role_rows) > 0:
                profile_role = role_rows.iloc[0]
                if pd.notna(profile_role) and profile_role in unique_bedarf_roles:
                    default_role_index = unique_bedarf_roles.index(profile_role)
        except Exception:
            default_role_index = None

    # Bedarf auswählen
    if len(unique_bedarf_roles) == 0:
        st.warning("Keine Bedarfs-Rollen in den Bedarfsdaten vorhanden.")
        st.stop()

    # Sicherstellen, dass default_role_index ein valider int ist
    if default_role_index is None or default_role_index < 0 or default_role_index >= len(unique_bedarf_roles):
        default_role_index = 0

    set_bedarf_role = st.selectbox(
        "Bedarfs-Rolle auswählen:", unique_bedarf_roles, index=default_role_index, key="bedarf_auswahl_1"
    )

    # Zeitpunkt auswählen
    filtered_timestamps_bedarf = data_bedarfe.index[
        data_bedarfe[COLUMN_ROLE] == set_bedarf_role
    ]

    if len(filtered_timestamps_bedarf) == 0:
        st.warning("Für die ausgewählte Rolle sind keine Bedarfs-Zeitpunkte vorhanden.")
        st.stop()

    if len(filtered_timestamps_bedarf) == 1:
        set_first_timestamp_bedarf = filtered_timestamps_bedarf[0]
        set_second_timestamp_bedarf = set_first_timestamp_bedarf
    else:
        set_first_timestamp_bedarf, set_second_timestamp_bedarf = st.select_slider(
            label = "Zeitpunkte für den Vergleich auswählen:",
            options = filtered_timestamps_bedarf,
            value = [min(filtered_timestamps_bedarf), max(filtered_timestamps_bedarf)],
            format_func=lambda x: x.strftime("%d.%m.%Y") if hasattr(x, "strftime") else str(x)
        )

st.markdown("")

# Erste Zeile mit zwei Diagrammen
col1, col2 = st.columns(2)

with col1:

    # Differenzen berechnen 
    differences_df = calculate_time_differences(
        set_id_active_profile,
        set_first_timestamp_active_profile,
        set_second_timestamp_active_profile,
    )

    if not differences_df.empty:
        # Diagramm Profil Entwicklung
        title = "Profil Entwicklung"
        fig = create_gap_analysis_chart(
            differences_df,
            title,
            "Differenz (Später - Früher)",
            title_font_size=16 + TITLE_FONT_SIZE_INCREASE,
        )

        if fig:
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(get_gap_analysis_legend("zeitvergleich"))
    else:
        st.warning("Keine Werte für die ausgewählten Zeitpunkte verfügbar.")

with col2:

    # Differenzen Bedarf Entwicklung
    data_bedarfe = data_bedarfe.reset_index()
    differences_bedarf_df = calculate_time_differences_bedarfe(
        data_bedarfe,
        set_bedarf_role,
        set_first_timestamp_bedarf,
        set_second_timestamp_bedarf,
    )

    if not differences_bedarf_df.empty:
        title = "Rolle Entwicklung"
        fig_bedarf = create_gap_analysis_chart(
            differences_bedarf_df,
            title,
            "Differenz (Später - Früher)",
            title_font_size=16 + TITLE_FONT_SIZE_INCREASE,
        )
        if fig_bedarf:
            st.plotly_chart(fig_bedarf, use_container_width=True)
            st.markdown(get_gap_analysis_legend("zeitvergleich"))
    else:
        st.warning("Keine Werte für die ausgewählten Bedarfs-Zeitpunkte verfügbar.")

st.markdown("")

# Zweite Zeile mit zwei Diagrammen
col3, col4 = st.columns(2)

with col3:

    # Gap zwischen Profil-Entwicklung und Bedarf-Entwicklung berechnen
    if not differences_df.empty and not differences_bedarf_df.empty:
        development_gap_df = calculate_development_gap(
            differences_df, differences_bedarf_df
        )

        # Aktuelle Gap-Werte zum Dataframe hinzufügen
        if not data_bedarfe.empty:
            # Differenzen berechnen mit modularer Funktion
            current_gap_df = calculate_cluster_differences(
                set_id_active_profile,
                set_bedarf_role,
                set_second_timestamp_active_profile,
                set_second_timestamp_bedarf,
            )
        else:
            current_gap_df = pd.DataFrame()
        current_gap_df.rename(columns={"Differenz": "Ist-Werte"}, inplace=True)
        combined_df = pd.merge(development_gap_df, current_gap_df, on="Cluster", how="inner")

        if not development_gap_df.empty:
            title = "Gap-Diagnose: Profil vs. Bedarf Entwicklung"
            fig_gap = create_gap_analysis_chart(
                combined_df,
                title,
                "Differenz (Profil-Entwicklung - Bedarf-Entwicklung)",
                title_font_size=16 + TITLE_FONT_SIZE_INCREASE,
            )
            if fig_gap:
                fig_gap.update_layout(height=500)
                st.plotly_chart(fig_gap, use_container_width=True)
                st.markdown(get_gap_analysis_legend("entwicklung_gap"))
        else:
            st.warning("Keine Daten für die Gap-Diagnose verfügbar.")
    else:
        st.warning(
            "Bitte stellen Sie sicher, dass sowohl Profil- als auch Bedarf-Entwicklungsdaten verfügbar sind."
        )

with col4:

    st.subheader("Korrelationen der Cluster")
    corr_data = get_cluster_values_for_correlation_matrix(data_answers_real)
    corr = corr_data.corr()

    #Diagonale entfernen
    corr_pairs = (
        corr.where(~np.eye(corr.shape[0], dtype=bool))  # Entfernt Diagonale
        .stack()
        .reset_index()
    )
    corr_pairs.columns = ["Variable 1", "Variable 2", "Korrelation"]

    #Sortieren und Entfernen der Duplikate
    corr_pairs["sorted_pair"] = corr_pairs.apply(lambda row: tuple(sorted([row["Variable 1"], row["Variable 2"]])),
                                                 axis=1)
    corr_pairs = corr_pairs.drop_duplicates("sorted_pair").drop(columns="sorted_pair")

    #Ordnen nach Korrelationswert
    corr_sorted = corr_pairs.sort_values("Korrelation", ascending=False)

    #Auswahl treffen
    top5 = corr_sorted.head(5)
    bottom5 = corr_sorted.tail(5)

    #Ausgabe
    st.markdown("#### Top 5:")
    for _, row in top5.iterrows():
        st.write(f"**{row['Variable 1']}** & **{row['Variable 2']}**: {row['Korrelation']:.2f}")

    st.markdown("#### Bottom 5:")
    for _, row in bottom5.iterrows():
        st.write(f"**{row['Variable 1']}** & **{row['Variable 2']}**: {row['Korrelation']:.2f}")

    st.markdown("")

    st.markdown("""
    #### Erläuterung:
    | Korrelationswert | Bedeutung                        |
    |------------------|----------------------------------|
    | +1,00            | Perfekte positive Korrelation    |
    | ~ +0,70          | Stark positive Korrelation       |
    | ~ +0,40          | Schwach positive Korrelation     |
    | 0                | Keine Korrelation                |
    | ~ -0,40          | Schwach negative Korrelation     |
    | ~ -0,70          | Stark negative Korrelation       |
    | -1,00            | Perfekte negative Korrelation    |
    """)

    #Suchfunktion nach Korrelation zwischen 2 beliebigen Kompetenzen
    st.markdown('#### Korrelation zwischen:')

    # Holen eindeutige Kompetenzen aus corr_pairs DataFrame
    variables = sorted(set(corr_pairs["Variable 1"]).union(set(corr_pairs["Variable 2"])))

    # Dropdown zur Wahl der Kompetenzen
    col1, col2 = st.columns(2)
    var1 = col1.selectbox("Erste Kompetenz auswählen", variables, key="var1_select")
    var2 = col2.selectbox("Zweite Kompetenz auswählen", variables, index=1, key="var2_select")

    # Korrelationswert nur bei unterschiedlichen Kompetenzen anzeigen
    if var1 != var2:

        # Korrelationswert holen
        search_pair = tuple(sorted([var1, var2]))
        
        mask = (
            ((corr_pairs["Variable 1"] == search_pair[0]) & (corr_pairs["Variable 2"] == search_pair[1])) |
            ((corr_pairs["Variable 1"] == search_pair[1]) & (corr_pairs["Variable 2"] == search_pair[0]))
        )
        match = corr_pairs[mask]

        if match.empty:
            st.warning(f"Keine Korrelation für {var1} und {var2} gefunden.")
            

        corr_value = match["Korrelation"].iloc[0]

        # Ausgabe
        st.metric(
            label=f"Korrelation zwischen **{var1}** und **{var2}**",
            value=f"{corr_value:.2f}"
        )

    # Errorausgabe beim identischen Kompetenzenwahl
    else:
        st.info("Wählen Sie bitte 2 unterschiedliche Kompetenzen")   


# Fußzeile
footer()
