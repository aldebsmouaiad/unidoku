# Datei zur Konfiguration von Variablen, die in mehreren Dateien verwendet werden können.

# -Fragebogen-
# Mögliche Antworten für die Fragen
OPTIONS_FORM = ("trifft nicht zu", "trifft eher nicht zu", "teils-teils", "trifft eher zu", "trifft zu")

# Mögliche Antworten für die Branchen (Sonstiges wird später hinzugefügt)
OPTIONS_INDUSTRY = [
    "Industrie / Produktion", 
    "Handwerk", "Handel", 
    "IT / Software / Digitalisierung", 
    "Gesundheitswesen / Soziale Dienste", 
    "Bildung / Wissenschaft / Forschung",
    "Bauwesen / Architektur",
    "Energie / Umwelt",
    "Logistik / Transport",
    "Öffentlicher Dienst / Verwaltung",
    "Dienstleistung allgemein"
]

# IDs der zusätzlichen Informationen
ADDITIONAL_INFORMATION_IDS = ["0SD01", "0SD01B", "0SD02", "0SD03", "0SD04", "0SD05", "0SD06"]

# Anzahl Fragen pro Seite im Fragebogen
AMOUNT_QUESTIONS_PER_PAGE = 12

# Übersetzungstabellen
TRANSLATE_ANSWER_SAVE = {
    "trifft nicht zu": 1, 
    "trifft eher nicht zu": 2, 
    "teils-teils": 3, 
    "trifft eher zu": 4, 
    "trifft zu": 5,
    None: 0
}
TRANSLATE_ANSWER_INDEX = {
    "trifft nicht zu": 0, 
    "trifft eher nicht zu": 1, 
    "teils-teils": 2, 
    "trifft eher zu": 3, 
    "trifft zu": 4,
    None: None
}

# Pfade zu Dateien
PATH_QUESTIONNAIRE = "fragebögen/2025-07-23_Finalversion_Fragebogen_pro-kom_aufbereitet_UTF-8.csv"
GOOGLE_SHEET_ANSWERS = "antworten"
GOOGLE_SHEET_ANSWERS_FRAGEBOGEN = "antworten_fragebogen" # Damit die Antworten aus dem Fragebogen den Testdatensatz nicht beeinflussen
GOOGLE_SHEET_PROFILES = "profile"
GOOGLE_SHEET_BEDARFE = "bedarfe"
GOOGLE_SHEET_GENERATED_DATA = "datengenerierung"


# Spaltennamen
COLUMN_TIMESTAMP = "Speicherzeitpunkt"
COLUMN_PROFILE_ID = "Profil-ID"
COLUMN_ROLE_ID = "Rollen-ID"
COLUMN_INDEX = "index"
COLUMN_ROLE = "Rollen-Name"

# Spaltennamen in Fragebogen
COLUMN_QUESTION_ID = "Frage-ID"
COLUMN_CLUSTER_NUMBER = "Cluster-Nummer"
COLUMN_CLUSTER_NAME = "Cluster-Name"
COLUMN_SUBSCALE = "Subskala"
COLUMN_QUESTION = "Frage"
COLUMN_INVERTED = "invertiert"



# Spaltennamen für die Cluster-Werte
CLUSTER_COLUMNS = ["cluster1", "cluster2", "cluster3", "cluster4", "cluster5", "cluster6", "cluster7", "cluster8", "cluster9", "cluster10", "cluster11"]

# Jahre, die in der Prognose berücksichtigt werden sollen
YEARS_TO_PREDICT = [2026, 2027, 2028, 2029, 2030]


# Texte für Fragebogen
INTRODUCTION_TEXT = '''Herzlich willkommen zur Kompetenzbefragung im Rahmen des Forschungsprojekts pro-kom!  
  
Ziel dieser Befragung ist es, ein besseres Verständnis dafür zu gewinnen, welche Kompetenzen in kleinen und mittleren Unternehmen (KMU) aktuell vorhanden sind – und welche künftig benötigt werden. Die Ergebnisse der Befragung bilden die Grundlage für die Entwicklung eines Prognosetools, das Unternehmen dabei unterstützt, frühzeitig auf zukünftige Kompetenzanforderungen zu reagieren. \n Mit Ihrer Teilnahme leisten Sie einen wertvollen Beitrag dazu, Unternehmen zukunftssicher aufzustellen. Gleichzeitig erhalten Sie am Ende der Befragung eine persönliche Rückmeldung über Ihre Kompetenzen sowie eine Einschätzung Ihrer individuellen Entwicklungspotenziale. \n In dieser Befragung werden verschiedene Kompetenzen abgefragt, darunter z. B. Fachkompetenz, Resilienz, Führungskompetenz, analytisches Denken und kommunikative Fähigkeiten. \n Die Teilnahme dauert ca. 40 Minuten. Die Daten werden ausschließlich für die genannten Forschungszwecke verarbeitet. Ihre Angaben werden vertraulich behandelt und gemäß den geltenden Datenschutzvorschriften (insbesondere DSGVO) gespeichert. Die Ergebnisse werden grundsätzlich in aggregierter Form ausgewertet. Eine Identifikation einzelner Personen ist dabei nicht möglich.  
  
Sie haben das Recht auf Auskunft über Ihre gespeicherten Daten, Berichtigung unzutreffender Angaben, Löschung oder Einschränkung der Verarbeitung sowie das Recht auf Datenübertragbarkeit. Darüber hinaus können Sie Ihre Einwilligung jederzeit ohne Angabe von Gründen mit Wirkung für die Zukunft widerrufen.
  
Wenn Sie Fragen haben oder weitere Informationen benötigen, schreiben Sie uns gerne eine E-Mail an Timon.Malirsch@fir.rwth-aachen.de  
  
Wir danken Ihnen herzlich für Ihre Unterstützung und Ihre Zeit!  
  
Ihr pro-kom Team  
  
Projektinformationen: Laufzeit: 01.03.2023 – 28.02.2025  
Förderkennzeichen: 22572 N  
Zuwendungsgeber: Bundesministerium für Wirtschaft und Energie (BMWE)  
Projektträger: DLR  
  
Förderhinweis: Das IGF-Vorhaben 22572 N der Forschungsvereinigung FIR e.V. an der RWTH Aachen und des RIF Instituts für Forschung und Transfer e.V. wird durch das Bundesministerium für Wirtschaft und Energie aufgrund eines Beschlusses des Deutschen Bundestages gefördert.'''

CONSENT_TEXT = '''Ich erkläre mich damit einverstanden, dass meine im Rahmen dieser Befragung erhobenen Daten anonymisiert zu wissenschaftlichen Forschungszwecken im Projekt pro-kom verwendet werden.  
Die Teilnahme ist freiwillig und kann jederzeit ohne Angabe von Gründen abgebrochen werden.'''

DEMOGRAPHY_TEXT = '''Um die Ergebnisse der Befragung besser einordnen zu können, bitten wir Sie im Folgenden um einige allgemeine Angaben zu Ihrer beruflichen Tätigkeit.  
Diese Daten werden ausschließlich anonymisiert ausgewertet und dienen dazu, die Befragungsergebnisse im Gesamtkontext besser interpretieren zu können.'''

INTRODUCTION_QUERRY = '''Im folgenden Abschnitt bitten wir Sie, verschiedene Aussagen zu beruflichen Kompetenzen einzuschätzen.  
Diese Kompetenzen sind in vielen Berufsfeldern von zentraler Bedeutung – unabhängig von Branche oder Position.  
  
Bitte geben Sie für jede Aussage an, inwieweit sie auf Sie zutrifft.  
Es gibt keine richtigen oder falschen Antworten. Wichtig ist Ihre persönliche Selbsteinschätzung – so ehrlich und spontan wie möglich.'''