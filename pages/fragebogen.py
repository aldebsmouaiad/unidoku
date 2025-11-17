import streamlit as st
import pandas as pd
import datetime as dt
import pytz
from config import AMOUNT_QUESTIONS_PER_PAGE, OPTIONS_FORM, TRANSLATE_ANSWER_SAVE, TRANSLATE_ANSWER_INDEX, PATH_QUESTIONNAIRE, ADDITIONAL_INFORMATION_IDS, GOOGLE_SHEET_ANSWERS_FRAGEBOGEN, COLUMN_PROFILE_ID, GOOGLE_SHEET_PROFILES, COLUMN_INDEX
from functions.menu import no_menu
from functions.page import footer
from functions.data import get_amount_questions, get_question_ids
from functions.session_state import clear_session_states_except_mode_and_debug_mode, check_mode
from functions.database import get_dataframe_from_gsheet, update_dataframe_to_gsheet

# -Seitenkonfiguration-
st.set_page_config(page_title="Fragebogen", layout="wide")
check_mode()
no_menu()

# -Profildaten einlesen-
data_profiles = get_dataframe_from_gsheet(GOOGLE_SHEET_PROFILES, index_col=COLUMN_PROFILE_ID)

# -Fragebogen einlesen-
fragebogen = pd.read_csv(PATH_QUESTIONNAIRE, sep=';', encoding='utf-8')

# -Funktionen-
def check_none_answers():
    none_counter = 0
    for question_id in question_ids_current_page:
        if st.session_state[f"answer_{question_id}"] is None:
            none_counter += 1
    if none_counter == 0:
        if "none_error" in st.session_state:
            del st.session_state.none_error
        return False
    else:
        if "none_error" not in st.session_state:
            st.session_state.none_error = True
        return True

def update_answers():
    for current_question_id in question_ids_current_page:
        st.session_state.current_answers[current_question_id] = st.session_state[f"answer_{current_question_id}"]
        del st.session_state[f"answer_{current_question_id}"]

def click_continue():
    if not check_none_answers():
        update_answers()
        st.session_state.page += 1

def click_back():
    if "none_error" in st.session_state:
        del st.session_state.none_error
    update_answers()
    st.session_state.page -= 1

def submit_form():
    try:
        # Tabelle für Antworten verknüpfen
        answers = get_dataframe_from_gsheet(GOOGLE_SHEET_ANSWERS_FRAGEBOGEN, index_col=COLUMN_INDEX)

        # Tabelle initialisieren
        questionnaire_id = answers.shape[0]
        timezone = pytz.timezone('Europe/Berlin')
        timestamp = dt.datetime.now(timezone)
        formatted_timestamp = timestamp.strftime('%d.%m.%Y %H:%M')
        data_new_answers = {
            "Speicherzeitpunkt": [formatted_timestamp],
            "Profil-ID": [st.session_state.id_active_profile]
        }

        # Zuerst demografische Antworten speichern
        for demo_id in ADDITIONAL_INFORMATION_IDS:
            antwort = st.session_state.current_answers.get(demo_id)
            data_new_answers[demo_id] = [str(antwort) if antwort is not None else ""]

        # Dann alle anderen Antworten speichern (außer Demographie)
        for answer_id, antwort in st.session_state.current_answers.items():
            if answer_id in ADDITIONAL_INFORMATION_IDS:
                continue  # Schon gespeichert
            if antwort in TRANSLATE_ANSWER_SAVE:
                # Fragebogen-Antworten (numerisch speichern)
                data_new_answers[answer_id] = [int(TRANSLATE_ANSWER_SAVE[antwort])]
            else:
                # Sonstige Antworten (als String speichern)
                data_new_answers[answer_id] = [str(antwort) if antwort is not None else ""]
        
        new_answers = pd.DataFrame(data_new_answers)
        new_answers.index = [questionnaire_id]

        # Tabellen kombinieren
        combined_answers = pd.concat([answers, new_answers], axis=0)

        # Tabelle in Google Sheets aktualisieren
        update_dataframe_to_gsheet(GOOGLE_SHEET_ANSWERS_FRAGEBOGEN, combined_answers)
        
        # Session States aufräumen
        clear_session_states_except_mode_and_debug_mode()
        
        st.success("Fragebogen erfolgreich gespeichert!")
        
    except Exception as e:
        st.error(f"Fehler beim Speichern des Fragebogens: {str(e)}")
        st.info("Ihre Antworten wurden temporär gespeichert. Bitte versuchen Sie es später erneut.")
        # Session States NICHT löschen, damit Antworten erhalten bleiben


# -Werte und Listen laden-
amount_questions = get_amount_questions()
question_ids = get_question_ids()

# -Titel-
st.title("Fragebogen")
st.write(f"Profil-ID: {st.session_state.id_active_profile if st.session_state.id_active_profile is not None else 'Keine'}")
st.write(f"Anzahl Fragen: {amount_questions}")

# -Anzahl der Seiten berechnen-
if amount_questions == 0:
    st.write("Es wurde kein Fragebogen hinterlegt.")
else:
    amount_pages = - ( - amount_questions // AMOUNT_QUESTIONS_PER_PAGE) # Aufgerundete, ganzzahlige Division
    st.write(f"Anzahl Seiten des Fragebogens: {amount_pages}")

# -Forschrittsanzeigen-
if 'page' not in st.session_state:
    st.session_state.page = 1
st.progress((st.session_state.page - 1) / amount_pages, text="Fortschritt Fragebogen")

# -Fragebogen-
def disable_submit_button():
    """
    Funktion den Submit-Button nach dem ersten Klick zu deaktivieren.
    """
    st.session_state.disabled_submit_button = True

if "disabled_submit_button" not in st.session_state:
    st.session_state.disabled_submit_button = False

with st.form("Fragebogen", enter_to_submit=False):
    if st.session_state.page < amount_pages:
        amount_questions_in_page = AMOUNT_QUESTIONS_PER_PAGE
    else:
        amount_questions_in_page = amount_questions - ((st.session_state.page - 1) * AMOUNT_QUESTIONS_PER_PAGE)
    st.header("Formular")
    st.write(f"Anzahl Fragen auf dieser Seite: {amount_questions_in_page}")
    question_ids_current_page = question_ids[(st.session_state.page - 1) * AMOUNT_QUESTIONS_PER_PAGE: ((st.session_state.page - 1) * AMOUNT_QUESTIONS_PER_PAGE) + amount_questions_in_page]
    for current_question_id in question_ids_current_page:
        with st.container(border=True):
            current_question_text = fragebogen.loc[fragebogen["Frage-ID"] == current_question_id, "Frage"].values[0]
            st.markdown(body = current_question_text)
            current_answer = st.session_state.current_answers[current_question_id]
            radio_button = st.radio(label=f"Frage {current_question_id}", options=OPTIONS_FORM, index=TRANSLATE_ANSWER_INDEX[current_answer], key=f"answer_{current_question_id}", horizontal=True, label_visibility="collapsed")
    st.write(f"Seite {st.session_state.page} von {amount_pages}")
    left, right = st.columns(2)
    if st.session_state.page < amount_pages:
        continue_button = right.form_submit_button(label="Weiter", on_click=click_continue)
    else:
        submit_button = right.form_submit_button(label="Fragebogen abschließen", on_click=disable_submit_button, disabled=st.session_state.disabled_submit_button)
        if submit_button:
            if not check_none_answers():
                update_answers()
                submit_form()
                st.switch_page("pages/fragebogen_ende.py")
    if st.session_state.page > 1:
        back_button = left.form_submit_button(label="Zurück", on_click=click_back)
    if "none_error" in st.session_state and st.session_state.none_error:
        st.warning("Bitte beantworten Sie alle Fragen.")

# Fußzeile
footer()
