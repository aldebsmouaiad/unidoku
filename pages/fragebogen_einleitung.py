import streamlit as st
import pandas as pd
import datetime as dt
import pytz
from config import INTRODUCTION_TEXT, CONSENT_TEXT, DEMOGRAPHY_TEXT, OPTIONS_INDUSTRY, INTRODUCTION_QUERRY, ADDITIONAL_INFORMATION_IDS, GOOGLE_SHEET_PROFILES, COLUMN_PROFILE_ID
from functions.menu import no_menu
from functions.page import footer
from functions.data import get_amount_questions, get_question_ids
from functions.session_state import clear_session_states_except_mode_and_debug_mode, check_mode
from functions.database import get_dataframe_from_gsheet, update_dataframe_to_gsheet
from functions.user_management import create_profile
from functions.initialize import initialize_fragebogen

# -Seitenkonfiguration-
st.set_page_config(page_title="Fragebogen", layout="wide")
check_mode()
no_menu()

# -Funktionen-
def check_errors():
    if st.session_state.einleitung_page == 2 and check_no_consent():
        return True
    elif st.session_state.einleitung_page == 4:
        fehlende = check_demography_complete()
        if fehlende:
            st.session_state.none_error = True
            st.session_state.fehlende_felder = fehlende
            return True
        else:
            if "fehlende_felder" in st.session_state:
                del st.session_state.fehlende_felder
    return False

def check_no_consent():
    if "answer_consent" in st.session_state and not st.session_state.answer_consent:
        st.session_state.consent_error = True
        return True
    else:
        return False

def check_demography_complete():
    fehlende_felder = []
    branche = st.session_state.get("answer_0SD01")
    branche_sonstige = st.session_state.get("answer_0SD01B", "")
    if branche is None:
        fehlende_felder.append("Branche")
    if branche == "Sonstige":
        if branche_sonstige is None or str(branche_sonstige).strip() == "":
            fehlende_felder.append("Branche (Wenn Sonstige)")
    else:
        if branche_sonstige is not None and str(branche_sonstige).strip() != "":
            fehlende_felder.append("'Branche (Wenn Sonstige)' darf nur bei Auswahl von 'Sonstige' befüllt sein)")
    abteilung = st.session_state.get("answer_0SD02", "")
    if abteilung is None or str(abteilung).strip() == "":
        fehlende_felder.append("Abteilung/Bereich")
    team_jahre = st.session_state.get("answer_0SD03")
    if team_jahre is None:
        fehlende_felder.append("Teamzugehörigkeit")
    unternehmen_jahre = st.session_state.get("answer_0SD04")
    if unternehmen_jahre is None:
        fehlende_felder.append("Unternehmenszugehörigkeit")
    personalverantwortung = st.session_state.get("answer_0SD05")
    if personalverantwortung not in ["Ja", "Nein"]:
        fehlende_felder.append("Personalverantwortung")
    alter = st.session_state.get("answer_0SD06")
    if alter is None:
        fehlende_felder.append("Alter")
    return fehlende_felder

def update_answers():
    """
    Zusätzliche Informationen in Session State speichern
    """
    # Demographische Antworten in current_answers speichern
    demographic_answers = {
        id: st.session_state.get(f"answer_{id}") # entspricht den Keys der Fragen
        for id in ADDITIONAL_INFORMATION_IDS
    }
    
    # current_answers initialisieren falls nicht vorhanden
    if "current_answers" not in st.session_state:
        st.session_state.current_answers = {}
    
    # Demographische Antworten hinzufügen
    for key, value in demographic_answers.items():
        if value is not None:
            st.session_state.current_answers[key] = value

def delete_errors():
    if "none_error" in st.session_state:
        del st.session_state.none_error
    if "consent_error" in st.session_state:
        del st.session_state.consent_error
    if "answer_consent" in st.session_state:
        del st.session_state.answer_consent
    if "fehlende_felder" in st.session_state:
        del st.session_state.fehlende_felder

def delete_local_session_states():
    """
    Löscht lokale Session States, die nicht mehr benötigt werden.
    """
    if "set_id_active_profile" in st.session_state:
        del st.session_state.set_id_active_profile
    for id in ADDITIONAL_INFORMATION_IDS:
        key = f"answer_{id}"
        if key in st.session_state:
            del st.session_state[key]

def click_continue():
    if not check_errors():
        delete_errors()
        update_answers()
        delete_local_session_states()
        st.session_state.einleitung_page += 1

def update_id_and_continue(new_id):
    st.session_state.id_active_profile = new_id
    click_continue()

def create_profile_and_continue(id, name):
    create_profile(id, name)
    update_id_and_continue(new_id=id)

def click_back():
    delete_errors()
    update_answers()
    delete_local_session_states()
    st.session_state.einleitung_page -= 1

# -Titel-
st.title("Fragebogen - Zusätzliche Informationen")

# -Inhalt der Seiten-
def page_1():
    st.header("Einleitung")
    st.markdown(INTRODUCTION_TEXT)
    left, right = st.columns(2)
    right.button(label="Weiter", on_click=click_continue)

def page_2():
    st.header("Zustimmung Datenschutz")
    st.markdown(CONSENT_TEXT)
    st.markdown("")
    st.checkbox(label="Ich stimme zu", value=False, key="answer_consent")
    left, right = st.columns(2)
    right.button(label="Weiter", on_click=click_continue)
    left.button(label="Zurück", on_click=click_back)
    if "consent_error" in st.session_state and st.session_state.consent_error:
        st.warning("Um fortzufahren, stimmen Sie bitte der Datenschutzerklärung zu.")

def page_3():
    st.header("Profil auswählen")

    # -Zwischengespeicherte Daten übernehmen-
    if "set_id_active_profile" not in st.session_state:
        st.session_state.set_id_active_profile = st.session_state.id_active_profile

    # -Erklärungstext-
    st.markdown("Unter dem ausgewählten Profil werden Ihre Antworten gespeichert. Falls Sie bereits einen Fragebogen ausgefüllt haben, nutzen Sie bitte Ihr bestehendes Profil. Falls Sie noch keinen Fragebogen ausgefüllt haben, erstellen Sie bitte ein neues Profil. Wenn Sie dies nicht möchten, dass Ihr Name gespeichert wird, können Sie ein Pseudonym verwenden.")

    # -Profildaten einlesen-
    data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)

    st.number_input(label="Profil-ID (zwischen 101 und 999):", min_value=101, max_value=999, key="set_id_active_profile")
    if "set_id_active_profile" in st.session_state and st.session_state.set_id_active_profile is not None:
        def reset_set_id_active_profile():
            st.session_state.set_id_active_profile = None
        left, right = st.columns(2)
        left.button(label="ID zurücksetzen", on_click=reset_set_id_active_profile)
        right.button(label="ID prüfen")
    else:
        st.button(label="ID prüfen")
    if st.session_state.set_id_active_profile is None:
        st.markdown("")
        left, right = st.columns(2)
        left.button(label="Zurück", on_click=click_back)
        right.button(label="Fortfahren", disabled=True)
    elif st.session_state.set_id_active_profile in data_profiles.index:
        st.write(f"Ein Profil mit der ID {st.session_state.set_id_active_profile} ist bereits vorhanden. Wenn Sie fortfahren, werden die Antworten in diesem Profil gespeichert.")
        st.markdown("")
        left, right = st.columns(2)
        left.button(label="Zurück", on_click=click_back)
        right.button(label="Mit Profil fortfahren", on_click=update_id_and_continue, kwargs={"new_id":st.session_state.set_id_active_profile})
    else:
        st.write(f"Kein Profil mit der ID {st.session_state.set_id_active_profile} gefunden. Bitte legen Sie ein neues Profil an, indem Sie einen Namen vergeben, wählen Sie ein andere ID aus oder setzen Sie die ID zurück, indem Sie die Eingabe unter Profil-ID löschen.")
        set_name_active_profile = st.text_input(label="Profil Name", value=None)
        st.button("Name prüfen")
        st.markdown("")
        left, right = st.columns(2)
        left.button(label="Zurück", on_click=click_back)
        right.button(label="Profil anlegen und fortfahren", disabled=not set_name_active_profile, on_click=create_profile_and_continue, kwargs={"id":st.session_state.set_id_active_profile, "name":set_name_active_profile})

def page_4():
    st.header("Demographie")

    # -Zwischengespeicherte Daten übernehmen-
    for id in ADDITIONAL_INFORMATION_IDS:
        if f"answer_{id}" not in st.session_state and "current_answers" in st.session_state and id in st.session_state.current_answers:
            st.session_state[f"answer_{id}"] = st.session_state.current_answers[id]
        elif f"answer_{id}" not in st.session_state:
            st.session_state[f"answer_{id}"] = None

    st.markdown(DEMOGRAPHY_TEXT)
    st.markdown("")
    branche_radio = st.radio(label="In welcher Branche ist Ihr Unternehmen hauptsächlich tätig?", options=OPTIONS_INDUSTRY + ["Sonstige"], key="answer_0SD01", index=None)
    if branche_radio == "Sonstige":
        st.text_input(label="Branche Sonstige", key="answer_0SD01B", value=None)
    else:
        if "answer_0SD01B" in st.session_state:
            del st.session_state.answer_0SD01B
    st.markdown("")
    st.text_input(label="In welcher Abteilung oder in welchem Bereich sind Sie zurzeit tätig?", key="answer_0SD02")
    st.number_input(label="Wie lange gehören Sie bereits Ihrem aktuellen Team an? (Bitte geben Sie die Anzahl der Jahre an.)", min_value=0.0, max_value=99.0, step=0.5, key="answer_0SD03")
    st.number_input(label="Wie lange arbeiten Sie bereits in Ihrem aktuellen Unternehmen?", min_value=0.0, max_value=99.0, step=0.5, key="answer_0SD04")
    st.radio(label="Haben Sie derzeit Personalverantwortung?", key="answer_0SD05", options=["Ja", "Nein"])
    st.number_input(label="Wie alt sind Sie? (optional: Bitte geben Sie 0 ein, falls Sie nicht antworten möchten.)", min_value=0, max_value=99, key="answer_0SD06") # TODO: Möglichkeit nicht zu beantworten?
    left, right = st.columns(2)
    left.button(label="Zurück", on_click=click_back)
    right.button(label="Weiter", on_click=click_continue)
    # Zeige Warnung, falls Felder fehlen
    if "fehlende_felder" in st.session_state and st.session_state.fehlende_felder:
        st.warning(f"Bitte beantworten Sie alle Felder: {', '.join(st.session_state.fehlende_felder)}")

def page_5():
    st.header("Einleitung Kompetenzabfrage")
    st.markdown(INTRODUCTION_QUERRY)
    left, right = st.columns(2)
    left.button(label="Zurück", on_click=click_back)
    begin_button = right.button(label="Fragebogen beginnen")
    if begin_button:
        initialize_fragebogen()
        st.switch_page("pages/fragebogen.py")

# Zuweisung der Seiten
pages_dict = {
    1: page_1,
    2: page_2,
    3: page_3,
    4: page_4,
    5: page_5
}

# -Aufrufen der Seiten-
with st.container(border=True):
    if st.session_state.einleitung_page in pages_dict:
        pages_dict[st.session_state.einleitung_page]()
    else:
        st.error("Fehler in der Verarbeitung: Ungültige Seite")

# Fußzeile
footer()
