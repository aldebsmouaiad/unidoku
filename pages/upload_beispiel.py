import streamlit as st
from functions.menu import default_menu, admin_check
from functions.page import footer
from functions.session_state import check_mode
from pathlib import Path

# -Seitenkonfiguration-
st.set_page_config(page_title="Upload Format", layout="wide")
check_mode()
admin_check()
default_menu()

# Dateien für den Download vorbereiten
base_dir = Path("upload_beispiel_dateien")
path_antworten = base_dir / "antworten.csv"
path_fragebogen = base_dir / "Fragebogen.csv"
path_profile = base_dir / "profile.csv"
path_rollen = base_dir / "rollen.csv"


# -Seiteninhalt-
st.title("Upload Format")

# -Download Buttons-
cols = st.columns(4)
with cols[0]:
    if path_fragebogen.exists():
        st.download_button(
            label="Download Fragebogen",
            data=path_fragebogen.read_bytes(),
            file_name=path_fragebogen.name,
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.warning("Fragebogen.csv nicht gefunden.")
with cols[1]:
    if path_antworten.exists():
        st.download_button(
            label="Download Antworten",
            data=path_antworten.read_bytes(),
            file_name=path_antworten.name,
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.warning("antworten.csv nicht gefunden.")
with cols[2]:
    if path_profile.exists():
        st.download_button(
            label="Download Profile",
            data=path_profile.read_bytes(),
            file_name=path_profile.name,
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.warning("profile.csv nicht gefunden.")
with cols[3]:
    if path_rollen.exists():
        st.download_button(
            label="Download Rollen-Bedarfe",
            data=path_rollen.read_bytes(),
            file_name=path_rollen.name,
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.warning("rollen.csv nicht gefunden.")

st.info(
    "Hier können Sie ein Beispiel für den Import Modus herunterladen.\n\n"
    "Die Fragen ID, welche mit 0 Beginnen sind Demographie Fragen. Diese können auch leer sein.\n\n"
    "- Unter 0SD01 wird die Branche (Vorauswahl) gespeichert.\n\n"
    "- Unter 0SD01B wird die Branche (Sonstiges) gespeichert.\n\n"
    "- Unter 0SD02 wird die Abteilung / der Bereich gespeichert.\n\n"
    "- Unter 0SD03 wird die Teamzugehörigkeit (in Jahren) gespeichert.\n\n"
    "- Unter 0SD04 wird die Unternehmenszugehörigkeit (in Jahren) gespeichert.\n\n"
    "- Unter 0SD05 wird die Personalverantwortung (Ja/Nein) gespeichert.\n\n"
    "- Unter 0SD06 wird das Alter gespeichert."
)

# Fußzeile
footer()
