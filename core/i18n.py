from __future__ import annotations

from typing import Any

import streamlit as st


LANGUAGE_KEY = "language"
LANGUAGE_OPTIONS = ("de", "en")


def normalize_language(value: Any) -> str:
    lang = str(value or "").strip().lower()
    if lang in ("en", "eng", "english"):
        return "en"
    return "de"


def init_language_state() -> None:
    if LANGUAGE_KEY not in st.session_state:
        st.session_state[LANGUAGE_KEY] = "de"
    else:
        st.session_state[LANGUAGE_KEY] = normalize_language(st.session_state[LANGUAGE_KEY])


def get_language() -> str:
    init_language_state()
    return normalize_language(st.session_state.get(LANGUAGE_KEY))


def set_language(language: Any) -> None:
    st.session_state[LANGUAGE_KEY] = normalize_language(language)


def language_option_label(language: Any) -> str:
    return "EN" if normalize_language(language) == "en" else "DE"


TRANSLATIONS: dict[str, dict[str, str]] = {
    "de": {
        "app.page_title": "Reifegradmodell Technische Dokumentation",
        "language.label": "Sprache",
        "sidebar.dark_mode": "Dunkelmodus",
        "sidebar.navigation": "Navigation",
        "sidebar.page_select": "Seite wählen",
        "privacy.title": "Datenschutz-Hinweis",
        "privacy.text": (
            "**Keine Speicherung:** Alle Eingaben bleiben nur während dieser Sitzung erhalten "
            "und werden nicht dauerhaft gespeichert.\n\n"
            "Für eine spätere Bearbeitung können Sie Ihren Zwischenspeicher als **JSON-Datei** "
            "herunterladen und später wieder hochladen."
        ),
        "privacy.accept": "Verstanden",
        "page.Start": "Start",
        "page.Einführung": "Einführung",
        "page.Ausfüllhinweise": "Ausfüllhinweise",
        "page.Erhebung": "Erhebung",
        "page.Dashboard": "Dashboard",
        "page.Priorisierung": "Priorisierung",
        "page.Gesamtübersicht": "Gesamtübersicht",
        "page.Glossar": "Glossar",
        "start.title": "Reifegradmodell für die Technische Dokumentation",
        "start.lead": (
            "Fragebasiertes Tool zur Bewertung und Weiterentwicklung der technischen Dokumentation "
            "– mit Auswertung, Priorisierung und Export (PDF/CSV/PNG/JSON)."
        ),
        "start.version": "Version",
        "start.status": "Stand",
        "start.time_required": "Zeitbedarf",
        "start.card.assessment.title": "Erhebung",
        "start.card.assessment.text": (
            "Beantworten Sie die Fragen je Subdimension und ermitteln Sie den Reifegrad stufenweise. "
            "Optional können Sie ein Zielniveau festlegen."
        ),
        "start.card.results.title": "Ergebnis",
        "start.card.results.text": (
            "Transparente Auswertung und Visualisierung des Reifegrads mit zentralen Kennzahlen "
            "und strukturierter Maßnahmenübersicht."
        ),
        "start.card.prioritization.title": "Priorisierung",
        "start.card.prioritization.text": (
            "Planen und bewerten Sie Maßnahmen nach Wirkung und Umsetzbarkeit – Fokus auf die wichtigsten Hebel."
        ),
        "start.card.export.title": "Export",
        "start.card.export.text": (
            "Exportieren Sie Ergebnisse als PDF-Bericht, CSV, PNG oder als wiederverwendbare JSON-Datei "
            "zum späteren Laden und Bearbeiten."
        ),
        "start.meta.created_by": "Erstellt durch",
        "start.meta.credit": "Credit",
        "start.meta.technical_support": "Technischer Support",
        "start.meta.validated_by": "Validiert durch",
        "start.meta.validated_with": "Validiert mit",
        "start.next_intro": "Weiter zu Einführung",
        "assessment.title": "Erhebung",
        "assessment.meta_title": "Angaben zur Erhebung",
        "assessment.questions_lead": "Bitte beantworten Sie die Fragen je Subdimension so objektiv wie möglich.",
        "assessment.time_notice": (
            "<b>Hinweis:</b> Für die vollständige Erhebung sollten Sie ca. 60 Minuten einplanen.<br>"
            "Der tatsächliche Aufwand kann je nach Organisation und vorhandenen Informationen variieren."
        ),
        "assessment.save_resume": "Speichern & Fortsetzen",
        "assessment.save_resume_caption": (
            "Speichern Sie Ihre Eingaben als JSON und laden Sie sie später wieder – "
            "z. B. für eine spätere Bearbeitung oder jährliche Wiedererhebung."
        ),
        "assessment.download_state": "Zwischenstand herunterladen",
        "assessment.upload_state": "Zwischenstand laden (JSON):",
        "assessment.load": "Laden",
        "assessment.field.org": "Name der Organisation:",
        "assessment.field.area": "Bereich:",
        "assessment.field.assessor": "Erhebung durchgeführt von:",
        "assessment.field.date": "Datum der Durchführung:",
        "assessment.field.target": "Angestrebtes Ziel:",
        "assessment.field.contact": "Kontakt:",
        "assessment.placeholder.org": "Beispiel GmbH",
        "assessment.placeholder.area": "Bereich A",
        "assessment.placeholder.assessor": "Herr/Frau Beispiel",
        "assessment.placeholder.contact": "name@organisation.de oder +49 ...",
        "assessment.start": "Erhebung starten",
        "assessment.define_custom_target": "Eigenes Ziel definieren",
        "assessment.edit_custom_target": "Eigenes Ziel ändern",
        "assessment.custom_target_defined": "Eigenes Ziel ist definiert.",
        "assessment.edit_meta": "Angaben bearbeiten",
        "assessment.instructions": "Ausfüllhinweise",
        "assessment.download_custom_target": "Eigenes Ziel herunterladen",
        "assessment.badge.org": "Organisation",
        "assessment.badge.area": "Bereich",
        "assessment.badge.date": "Datum",
        "assessment.badge.target": "Ziel",
        "assessment.badge.email": "E-Mail",
        "assessment.navigation": "Navigation",
        "assessment.jump_dimension": "Zu Dimension springen",
        "assessment.back": "◀ Zurück",
        "assessment.next": "Weiter ▶",
        "assessment.to_dashboard": "Zum Dashboard ▶",
        "assessment.progress": "Fortschritt",
        "assessment.level": "Stufe",
        "assessment.process_profile": "Prozess-Steckbrief",
        "assessment.acceptance_benefit": "Abnahmekriterien & Nutzen bei Erreichen der Stufe",
        "assessment.acceptance_criteria": "Abnahmekriterien",
        "assessment.benefit": "Nutzen bei Erreichen der Stufe",
        "assessment.level_locked": "Stufe {level} ist noch gesperrt, weil Stufe {prev} noch nicht erreicht wurde.",
        "assessment.custom_target_title": "Eigenes Ziel definieren",
        "assessment.custom_target_lead": "Zielniveau je Subdimension",
        "assessment.custom_target_body": (
            "Bitte wählen Sie für jede Subdimension den angestrebten Reifegrad zwischen 1 und 5. "
            "Optional können Sie vorhandene Zielwerte importieren oder exportieren."
        ),
        "assessment.import": "Import",
        "assessment.export": "Export",
        "assessment.upload_custom_target": "Eigenes Ziel hochladen (JSON oder CSV):",
        "assessment.import_button": "Importieren",
        "assessment.download_available": "Download ist verfügbar, sobald Werte vorhanden sind (Import oder Speicherung).",
        "assessment.search_label": "Suche nach Kürzel oder Subdimension:",
        "assessment.search_placeholder": "z. B. TD1.1 oder Redaktionsprozess",
        "assessment.no_search_results": "Keine Treffer für die aktuelle Suche.",
        "assessment.code": "Kürzel",
        "assessment.subdimension": "Subdimension",
        "assessment.custom_target": "Eigenes Ziel",
        "assessment.save_changes": "Änderungen speichern",
        "assessment.save_custom_target": "Eigenes Ziel speichern",
        "assessment.custom_target_saved": "Eigenes Ziel wurde gespeichert. Sie können jetzt die Erhebung starten.",
        "assessment.custom_target_unsaved": (
            "Bitte „Änderungen speichern“ klicken, damit diese Werte in der Erhebung verwendet werden."
        ),
        "assessment.no_dimensions": "Keine Subdimensionen gefunden (Model-Konfiguration leer).",
        "common.back": "Zurück",
        "common.close": "Schließen",
        "common.download": "Herunterladen",
        "common.fullscreen": "Vollbild",
        "common.no_data": "Keine Daten vorhanden.",
        "common.no_results": "Noch keine Ergebnisse vorhanden.",
        "common.no_results_assessment": "Noch keine Ergebnisse vorhanden – bitte zuerst die Erhebung durchführen.",
        "common.no_entries_available": "Keine Einträge vorhanden.",
        "common.no_entries_filter": "Keine Einträge passend zur aktuellen Auswahl.",
        "common.legend": "Legende:",
        "common.initial": "Initial",
        "common.managed": "Gemanagt",
        "common.defined": "Definiert",
        "common.quant_managed": "Quantitativ gemanagt",
        "common.optimized": "Optimiert",
        "column.code": "Kürzel",
        "column.topic": "Themenbereich",
        "column.current_level": "Ist-Reifegrad",
        "column.target_level": "Soll-Reifegrad",
        "column.priority": "Priorität",
        "column.measure": "Maßnahme",
        "column.responsible": "Verantwortlich",
        "column.timeframe": "Zeitraum",
        "column.gap": "Gap",
        "chart.current_level": "Ist-Reifegrad",
        "chart.target_level": "Soll-Reifegrad",
        "chart.current_short": "Ist",
        "chart.target_short": "Soll",
        "chart.toggle_current": "Ist-Reifegrad ein-/ausblenden",
        "chart.toggle_target": "Soll-Reifegrad ein-/ausblenden",
        "dashboard.lead": "Visualisiertes Ergebnis der Reifegraderhebung.",
        "dashboard.visualized": "Visualisiertes Ergebnis der Reifegraderhebung",
        "dashboard.table": "Ergebnis in Tabellenform",
        "dashboard.next_prioritization": "Weiter zur Priorisierung",
        "prioritization.title": "Priorisierung & Maßnahmenplanung",
        "prioritization.lead": "Legen Sie für jede Dimension fest, wie wichtig sie ist und welche konkreten Maßnahmen Sie angehen möchten.",
        "prioritization.dialog_title": "Maßnahmen-Vorschläge",
        "prioritization.dialog_meta": "Dimension",
        "prioritization.suggestions": "Vorschläge",
        "prioritization.no_suggestions": "Keine Vorschläge vorhanden.",
        "prioritization.pool_notice": (
            "**Hinweis (Maßnahmen-Pool):**\n\n"
            "Sie können optional Ihre eingegebenen Maßnahmen **als Vorschläge für andere Nutzer** bereitstellen.\n"
            "Wenn Sie zustimmen, wird **ausschließlich der Text im Feld „Maßnahme“** gespeichert.\n\n"
            "Bitte tragen Sie dort **keine sensiblen Daten** ein."
        ),
        "prioritization.share_question": "Möchten Sie Ihre Maßnahmen speichern und als Vorschläge für andere Nutzer zur Verfügung stellen?",
        "prioritization.yes": "Ja",
        "prioritization.no": "Nein",
        "prioritization.category": "Kategorie",
        "prioritization.all": "Alle",
        "prioritization.show_all": "Alle Dimensionen anzeigen (auch Gap ≤ 0)",
        "prioritization.no_action_dims": "Keine Dimensionen mit Handlungsbedarf (Gap > 0) in der aktuellen Filterauswahl.",
        "prioritization.gap_pill": "Gap (Soll–Ist)",
        "prioritization.level_units": "Reifegradstufen",
        "prioritization.priority_help": "A = hoch, B = mittel, C = niedrig",
        "prioritization.measure_placeholder": "z. B. Redaktionsleitfaden erstellen",
        "prioritization.suggestions_help": "Vorschläge anzeigen",
        "prioritization.responsible_placeholder": "z. B. Christian Koch",
        "prioritization.timeframe_placeholder": "z. B. Q1/2026",
        "prioritization.apply": "Priorisierungen übernehmen",
        "prioritization.apply_success": "Priorisierungen wurden übernommen.",
        "prioritization.apply_success_submitted": "Priorisierungen übernommen. {created} Vorschlag/Vorschläge automatisch übermittelt ({skipped} übersprungen).",
        "prioritization.apply_warning_submit": "Priorisierungen übernommen, aber die Übermittlung der Vorschläge ist fehlgeschlagen: {error}",
        "prioritization.unsaved": "Sie haben Priorisierungen geändert, die noch nicht übernommen wurden. Bitte zuerst „Priorisierungen übernehmen“ klicken, damit diese Werte verwendet werden.",
        "prioritization.next_overview": "Weiter zur Gesamtübersicht",
        "glossary.title": "Glossar",
        "glossary.lead": "Hier finden Sie Definitionen zu zentralen Begriffen und Abkürzungen. Nutzen Sie die Suche oder klappen Sie Einträge auf.",
        "glossary.search": "Suche",
        "glossary.placeholder": "Begriff eingeben…",
        "overview.title": "Gesamtübersicht",
        "overview.lead": "Zusammenfassung der Angaben zur Erhebung, visualisierte Ergebnisse und geplante Maßnahmen.",
        "overview.meta_title": "Angaben zur Erhebung",
        "overview.kpis": "Kennzahlen",
        "overview.assessed": "Bewertet",
        "overview.need_action": "Handlungsbedarf (Gap > 0)",
        "maturity.overall": "Gesamtreifegrad",
        "maturity.technical_documentation": "Technische Dokumentation",
        "maturity.organization": "Organisation",
        "maturity.average_current": "Durchschnitt Ist-Reifegrad",
        "maturity.valid_values": "{count} gültige Werte",
        "maturity.no_values": "Keine gültigen Ist-Werte",
        "overview.measures": "Geplante Maßnahmen",
        "overview.filter": "Filter",
        "overview.show_all": "Alle anzeigen (inkl. ohne Handlungsbedarf)",
        "overview.priority_filter": "Priorität filtern",
        "overview.priority_placeholder": "Prioritäten auswählen …",
        "overview.export": "Export",
        "overview.pdf_download": "PDF-Bericht herunterladen",
        "overview.pdf_unavailable": "PDF-Export nicht verfügbar: {error}",
        "overview.save_json": "Sitzung speichern (JSON)",
        "overview.unknown_org": "unbekannte_org",
        "assessment.save_json_info": "Speichert den aktuellen Stand als JSON-Datei auf Ihrem Gerät.",
        "assessment.load_overwrite_info": "Beim Laden wird der aktuelle Stand durch die Datei ersetzt.",
        "assessment.import_success": "Import erfolgreich: Antworten übernommen.",
        "assessment.upload_json_csv": "Bitte eine .json oder .csv Datei hochladen.",
        "assessment.unsaved_custom_target": "Es gibt ungespeicherte Änderungen im Eigenen Ziel. Bitte erst speichern.",
        "assessment.error_org_required": "Bitte den Namen der Organisation angeben.",
        "assessment.error_assessor_required": "Bitte angeben, wer die Erhebung durchgeführt hat.",
        "assessment.error_date_format": "Datum bitte im Format TT.MM.JJJJ eingeben (z. B. 03.12.2025).",
        "assessment.error_define_custom_target": "Bitte zuerst „Eigenes Ziel definieren“.",
        "assessment.custom_target_missing": "Eigenes Ziel ist nicht definiert. Bitte zuerst „Eigenes Ziel definieren“.",
        "assessment.custom_target_no_value": "Für diese Subdimension wurde kein Ziel gefunden. Bitte „Eigenes Ziel ändern“ nutzen.",
        "assessment.custom_target_level": "Eigenes Sollniveau:",
        "assessment.target_level": "Sollniveau:",
        "assessment.custom_target_caption": "Änderungen am Eigenen Ziel bitte über „Eigenes Ziel ändern“ durchführen.",
        "assessment.predefined_target_caption": "Vordefiniertes Ziel. Änderungen bitte über „Angaben bearbeiten“ vornehmen.",
        "assessment.profile.purpose": "Zweck",
        "assessment.profile.results": "Ergebnisse",
        "assessment.profile.basic_practices": "Basispraktiken",
        "assessment.profile.work_products": "Arbeitsprodukte",
    },
    "en": {
        "app.page_title": "Technical Documentation Maturity Model",
        "language.label": "Language",
        "sidebar.dark_mode": "Dark mode",
        "sidebar.navigation": "Navigation",
        "sidebar.page_select": "Choose page",
        "privacy.title": "Privacy Notice",
        "privacy.text": (
            "**No storage:** All entries remain available only during this session and are not stored permanently.\n\n"
            "For later editing, you can download your current progress as a **JSON file** and upload it again later."
        ),
        "privacy.accept": "Got it",
        "page.Start": "Start",
        "page.Einführung": "Introduction",
        "page.Ausfüllhinweise": "Instructions",
        "page.Erhebung": "Assessment",
        "page.Dashboard": "Dashboard",
        "page.Priorisierung": "Prioritization",
        "page.Gesamtübersicht": "Overview",
        "page.Glossar": "Glossary",
        "start.title": "Maturity Model for Technical Documentation",
        "start.lead": (
            "Questionnaire-based tool for assessing and improving technical documentation, including analysis, "
            "prioritization, and export (PDF/CSV/PNG/JSON)."
        ),
        "start.version": "Version",
        "start.status": "Updated",
        "start.time_required": "Time required",
        "start.card.assessment.title": "Assessment",
        "start.card.assessment.text": (
            "Answer the questions for each subdimension and determine the maturity level step by step. "
            "Optionally, define a target level."
        ),
        "start.card.results.title": "Results",
        "start.card.results.text": (
            "Transparent evaluation and visualization of maturity levels with key indicators and a structured action overview."
        ),
        "start.card.prioritization.title": "Prioritization",
        "start.card.prioritization.text": (
            "Plan and evaluate actions by impact and feasibility, focusing on the most important levers."
        ),
        "start.card.export.title": "Export",
        "start.card.export.text": (
            "Export results as a PDF report, CSV, PNG, or reusable JSON file for later loading and editing."
        ),
        "start.meta.created_by": "Created by",
        "start.meta.credit": "Credit",
        "start.meta.technical_support": "Technical support",
        "start.meta.validated_by": "Validated by",
        "start.meta.validated_with": "Validated with",
        "start.next_intro": "Continue to introduction",
        "assessment.title": "Assessment",
        "assessment.meta_title": "Assessment Details",
        "assessment.questions_lead": "Please answer the questions for each subdimension as objectively as possible.",
        "assessment.time_notice": (
            "<b>Note:</b> Please allow approximately 60 minutes for the complete assessment.<br>"
            "The actual effort may vary depending on the organization and the information available."
        ),
        "assessment.save_resume": "Save & Resume",
        "assessment.save_resume_caption": (
            "Save your entries as JSON and upload them again later, for example to continue editing "
            "or repeat the assessment annually."
        ),
        "assessment.download_state": "Download progress",
        "assessment.upload_state": "Load progress (JSON):",
        "assessment.load": "Load",
        "assessment.field.org": "Organization name:",
        "assessment.field.area": "Area:",
        "assessment.field.assessor": "Assessment conducted by:",
        "assessment.field.date": "Date of assessment:",
        "assessment.field.target": "Target level:",
        "assessment.field.contact": "Contact:",
        "assessment.placeholder.org": "Example Ltd.",
        "assessment.placeholder.area": "Area A",
        "assessment.placeholder.assessor": "Jane/John Doe",
        "assessment.placeholder.contact": "name@organization.com or +49 ...",
        "assessment.start": "Start assessment",
        "assessment.define_custom_target": "Define custom target",
        "assessment.edit_custom_target": "Edit custom target",
        "assessment.custom_target_defined": "Custom target is defined.",
        "assessment.edit_meta": "Edit details",
        "assessment.instructions": "Instructions",
        "assessment.download_custom_target": "Download custom target",
        "assessment.badge.org": "Organization",
        "assessment.badge.area": "Area",
        "assessment.badge.date": "Date",
        "assessment.badge.target": "Target",
        "assessment.badge.email": "Email",
        "assessment.navigation": "Navigation",
        "assessment.jump_dimension": "Jump to dimension",
        "assessment.back": "◀ Back",
        "assessment.next": "Next ▶",
        "assessment.to_dashboard": "To dashboard ▶",
        "assessment.progress": "Progress",
        "assessment.level": "Level",
        "assessment.process_profile": "Process Profile",
        "assessment.acceptance_benefit": "Acceptance Criteria & Benefit When Reaching This Level",
        "assessment.acceptance_criteria": "Acceptance criteria",
        "assessment.benefit": "Benefit when reaching this level",
        "assessment.level_locked": "Level {level} is still locked because level {prev} has not yet been reached.",
        "assessment.custom_target_title": "Define Custom Target",
        "assessment.custom_target_lead": "Target level by subdimension",
        "assessment.custom_target_body": (
            "Please choose the desired maturity level from 1 to 5 for each subdimension. "
            "Optionally, you can import or export existing target values."
        ),
        "assessment.import": "Import",
        "assessment.export": "Export",
        "assessment.upload_custom_target": "Upload custom target (JSON or CSV):",
        "assessment.import_button": "Import",
        "assessment.download_available": "Download is available as soon as values exist (import or save).",
        "assessment.search_label": "Search by code or subdimension:",
        "assessment.search_placeholder": "e.g., TD1.1 or editorial process",
        "assessment.no_search_results": "No results for the current search.",
        "assessment.code": "Code",
        "assessment.subdimension": "Subdimension",
        "assessment.custom_target": "Custom target",
        "assessment.save_changes": "Save changes",
        "assessment.save_custom_target": "Save custom target",
        "assessment.custom_target_saved": "Custom target has been saved. You can now start the assessment.",
        "assessment.custom_target_unsaved": "Please click “Save changes” so these values are used in the assessment.",
        "assessment.no_dimensions": "No subdimensions found (model configuration is empty).",
        "common.back": "Back",
        "common.close": "Close",
        "common.download": "Download",
        "common.fullscreen": "Full screen",
        "common.no_data": "No data available.",
        "common.no_results": "No results available yet.",
        "common.no_results_assessment": "No results available yet. Please complete the assessment first.",
        "common.no_entries_available": "No entries available.",
        "common.no_entries_filter": "No entries match the current selection.",
        "common.legend": "Legend:",
        "common.initial": "Initial",
        "common.managed": "Managed",
        "common.defined": "Defined",
        "common.quant_managed": "Quantitatively managed",
        "common.optimized": "Optimized",
        "column.code": "Code",
        "column.topic": "Topic",
        "column.current_level": "Current maturity level",
        "column.target_level": "Target maturity level",
        "column.priority": "Priority",
        "column.measure": "Measure",
        "column.responsible": "Responsible",
        "column.timeframe": "Timeframe",
        "column.gap": "Gap",
        "chart.current_level": "Current maturity level",
        "chart.target_level": "Target maturity level",
        "chart.current_short": "Current",
        "chart.target_short": "Target",
        "chart.toggle_current": "Toggle current maturity level",
        "chart.toggle_target": "Toggle target maturity level",
        "dashboard.lead": "Visualized result of the maturity assessment.",
        "dashboard.visualized": "Visualized result of the maturity assessment",
        "dashboard.table": "Results table",
        "dashboard.next_prioritization": "Continue to prioritization",
        "prioritization.title": "Prioritization & Action Planning",
        "prioritization.lead": "Set the importance of each dimension and define the specific measures you want to address.",
        "prioritization.dialog_title": "Measure Suggestions",
        "prioritization.dialog_meta": "Dimension",
        "prioritization.suggestions": "Suggestions",
        "prioritization.no_suggestions": "No suggestions available.",
        "prioritization.pool_notice": (
            "**Note (measure pool):**\n\n"
            "You can optionally provide your entered measures **as suggestions for other users**.\n"
            "If you agree, **only the text in the Measure field** will be stored.\n\n"
            "Please do **not** enter sensitive data there."
        ),
        "prioritization.share_question": "Would you like to save your measures and make them available as suggestions for other users?",
        "prioritization.yes": "Yes",
        "prioritization.no": "No",
        "prioritization.category": "Category",
        "prioritization.all": "All",
        "prioritization.show_all": "Show all dimensions (including gap ≤ 0)",
        "prioritization.no_action_dims": "No dimensions with action needed (gap > 0) in the current filter selection.",
        "prioritization.gap_pill": "Gap (target-current)",
        "prioritization.level_units": "maturity levels",
        "prioritization.priority_help": "A = high, B = medium, C = low",
        "prioritization.measure_placeholder": "e.g. create an editorial guideline",
        "prioritization.suggestions_help": "Show suggestions",
        "prioritization.responsible_placeholder": "e.g. Christian Koch",
        "prioritization.timeframe_placeholder": "e.g. Q1/2026",
        "prioritization.apply": "Apply priorities",
        "prioritization.apply_success": "Priorities have been applied.",
        "prioritization.apply_success_submitted": "Priorities applied. {created} suggestion(s) submitted automatically ({skipped} skipped).",
        "prioritization.apply_warning_submit": "Priorities were applied, but submitting the suggestions failed: {error}",
        "prioritization.unsaved": "You have changed priorities that have not been applied yet. Please click “Apply priorities” first so these values are used.",
        "prioritization.next_overview": "Continue to overview",
        "glossary.title": "Glossary",
        "glossary.lead": "Find definitions for key terms and abbreviations. Use search or expand entries.",
        "glossary.search": "Search",
        "glossary.placeholder": "Enter term…",
        "overview.title": "Overview",
        "overview.lead": "Summary of assessment details, visualized results, and planned measures.",
        "overview.meta_title": "Assessment Details",
        "overview.kpis": "Key Figures",
        "overview.assessed": "Assessed",
        "overview.need_action": "Action needed (gap > 0)",
        "maturity.overall": "Overall maturity level",
        "maturity.technical_documentation": "Technical Documentation",
        "maturity.organization": "Organization",
        "maturity.average_current": "Average current maturity level",
        "maturity.valid_values": "{count} valid values",
        "maturity.no_values": "No valid current values",
        "overview.measures": "Planned Measures",
        "overview.filter": "Filter",
        "overview.show_all": "Show all (including no action needed)",
        "overview.priority_filter": "Filter priority",
        "overview.priority_placeholder": "Select priorities …",
        "overview.export": "Export",
        "overview.pdf_download": "Download PDF report",
        "overview.pdf_unavailable": "PDF export unavailable: {error}",
        "overview.save_json": "Save session (JSON)",
        "overview.unknown_org": "unknown_org",
        "assessment.save_json_info": "Saves the current progress as a JSON file on your device.",
        "assessment.load_overwrite_info": "Loading replaces the current progress with the file contents.",
        "assessment.import_success": "Import successful: answers have been applied.",
        "assessment.upload_json_csv": "Please upload a .json or .csv file.",
        "assessment.unsaved_custom_target": "There are unsaved changes in the custom target. Please save first.",
        "assessment.error_org_required": "Please enter the organization name.",
        "assessment.error_assessor_required": "Please enter who conducted the assessment.",
        "assessment.error_date_format": "Please enter the date in DD.MM.YYYY format (e.g. 03.12.2025).",
        "assessment.error_define_custom_target": "Please define the custom target first.",
        "assessment.custom_target_missing": "Custom target is not defined. Please define the custom target first.",
        "assessment.custom_target_no_value": "No target was found for this subdimension. Please use “Edit custom target”.",
        "assessment.custom_target_level": "Custom target level:",
        "assessment.target_level": "Target level:",
        "assessment.custom_target_caption": "Change the custom target via “Edit custom target”.",
        "assessment.predefined_target_caption": "Predefined target. Please use “Edit details” to make changes.",
        "assessment.profile.purpose": "Purpose",
        "assessment.profile.results": "Results",
        "assessment.profile.basic_practices": "Basic practices",
        "assessment.profile.work_products": "Work products",
    },
}


TARGET_OPTION_LABELS = {
    "Eigenes Ziel": {"de": "Eigenes Ziel", "en": "Custom target"},
    "Optimiert": {"de": "Optimiert", "en": "Optimized"},
    "Quantitativ gemanagt": {"de": "Quantitativ gemanagt", "en": "Quantitatively managed"},
    "Definiert": {"de": "Definiert", "en": "Defined"},
    "Gemanagt": {"de": "Gemanagt", "en": "Managed"},
}

ANSWER_OPTION_LABELS = {
    "Nicht anwendbar": {"de": "Nicht anwendbar", "en": "Not applicable"},
    "Gar nicht": {"de": "Gar nicht", "en": "Not at all"},
    "In ein paar Fällen": {"de": "In ein paar Fällen", "en": "In a few cases"},
    "In den meisten Fällen": {"de": "In den meisten Fällen", "en": "In most cases"},
    "Vollständig": {"de": "Vollständig", "en": "Fully"},
}

PRIORITY_OPTION_LABELS = {
    "": {"de": "— auswählen —", "en": "— select —"},
    "A (hoch)": {"de": "A · hoch", "en": "A · high"},
    "B (mittel)": {"de": "B · mittel", "en": "B · medium"},
    "C (niedrig)": {"de": "C · niedrig", "en": "C · low"},
}

PRIORITY_VALUE_LABELS = {
    "A (hoch)": {"de": "A (hoch)", "en": "A (high)"},
    "B (mittel)": {"de": "B (mittel)", "en": "B (medium)"},
    "C (niedrig)": {"de": "C (niedrig)", "en": "C (low)"},
}


def t(key: str, *, language: Any | None = None) -> str:
    lang = normalize_language(language) if language is not None else get_language()
    return TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["de"].get(key) or key


def page_label(page_key: str) -> str:
    return t(f"page.{page_key}")


def target_option_label(value: Any) -> str:
    text = str(value)
    lang = get_language()
    return TARGET_OPTION_LABELS.get(text, {}).get(lang, text)


def answer_option_label(value: Any) -> str:
    text = str(value)
    lang = get_language()
    return ANSWER_OPTION_LABELS.get(text, {}).get(lang, text)


def priority_option_label(value: Any) -> str:
    text = str(value)
    lang = get_language()
    return PRIORITY_OPTION_LABELS.get(text, {}).get(lang, text)


def priority_value_label(value: Any) -> str:
    text = str(value)
    lang = get_language()
    return PRIORITY_VALUE_LABELS.get(text, {}).get(lang, text)
