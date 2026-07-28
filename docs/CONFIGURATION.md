# Konfiguration

Diese Datei beschreibt die tatsächlich vorhandenen Konfigurationsmöglichkeiten des Projekts. Die Anwendung wird
hauptsächlich über JSON-Dateien unter `data/`, Übersetzungen in `core/i18n.py`, Scoring-Regeln in `core/scoring.py`
und Streamlit-Secrets für die optionale GitHub-Integration konfiguriert.

## Wichtige Dateien

```text
data/models/niro_td_model.json
data/models/niro_td_model_en.json
data/niro_td_meta.json
data/niro_td_meta_en.json
data/measures.json
core/i18n.py
core/scoring.py
pages/01_Erhebung.py
pages/03_Priorisierung.py
.streamlit/config.toml
.streamlit/secrets.toml
```

`.streamlit/secrets.toml` ist nicht im Repository enthalten und wird durch `.gitignore` ausgeschlossen.

## Sprachumschaltung

Die App unterstützt Deutsch und Englisch. Die Sprache entscheidet, welche Modell- und Metadaten-Dateien geladen werden:

- Deutsch: `data/models/niro_td_model.json` und `data/niro_td_meta.json`
- Englisch: `data/models/niro_td_model_en.json` und `data/niro_td_meta_en.json`

Die UI-Texte liegen in `core/i18n.py`. Neue UI-Texte müssen dort in beiden Sprachen ergänzt werden.

## Modell-Dateien

Die Modell-Dateien haben dieselbe Struktur:

```text
name
description
levels_info
glossary
dimensions
```

Aktueller Umfang beider Modell-Dateien:

- 33 Dimensionen
- 165 Reifegradstufen
- 434 Fragen

## Struktur einer Dimension

Eine Dimension enthält diese Felder:

```json
{
  "code": "TD1.1",
  "name": "Redaktionsprozess - Prozessinitiierung",
  "category": "TD",
  "description": "...",
  "default_target_level": 3,
  "process_profile": {
    "purpose": "...",
    "results": "...",
    "basic_practices": "...",
    "work_products": "..."
  },
  "levels": []
}
```

Verwendete Kategorien im vorhandenen Modell:

- `TD` für Technische Dokumentation
- `OG` für Organisation

Der `code` ist die zentrale Kennung einer Dimension. Er wird unter anderem für Antworten, Zielwerte, Maßnahmen, Tabellen, Diagramme und Exporte verwendet. Codes sollten deshalb stabil bleiben.

## Struktur einer Reifegradstufe

Jede Dimension enthält fünf Level. Ein Level enthält diese Felder:

```json
{
  "level_number": 1,
  "name": "initial",
  "acceptance_criteria": "...",
  "benefit": "...",
  "questions": []
}
```

`level_number` wird für Sortierung und Reifegradlogik verwendet. Die vorhandenen Modelle nutzen die Stufen `1` bis `5`.

## Struktur einer Frage

Eine Frage enthält diese Felder:

```json
{
  "id": "TD1.1-L1-Q1",
  "text": "..."
}
```

Die `id` ist die technische Kennung der Frage und wird im Session-State sowie in exportierten Zwischenständen
verwendet. Eine Änderung bestehender IDs kann dazu führen, dass alte Zwischenstände nicht mehr sauber zugeordnet
werden können.

## Antwortskala

Die Antwortoptionen werden in `pages/01_Erhebung.py` definiert und in `core/scoring.py` bewertet.

Interne Antwortwerte:

```text
Nicht anwendbar
Gar nicht
In ein paar Fällen
In den meisten Fällen
Vollständig
```

Scoring in `core/scoring.py`:

```text
Vollständig              -> 1.0
In den meisten Fällen    -> 0.75
In ein paar Fällen       -> 0.5
Gar nicht                -> 0.0
Nicht anwendbar          -> aus dem Nenner entfernen
```

Wichtig: Die internen Antwortwerte sind deutschsprachige Strings. Die englischen Bezeichnungen werden über
`core/i18n.py` nur für die Anzeige übersetzt. Wer die Antwortoptionen ändert, muss mindestens
`pages/01_Erhebung.py`, `core/scoring.py` und `core/i18n.py` gemeinsam prüfen.

## Berechnungslogik

Die zentrale Reifegradberechnung liegt in `core/scoring.py` in `compute_dimension_maturity`.

Belegte Regeln aus dem Code:

- Nicht beantwortete Fragen zählen konservativ als `0.0`.
- `Nicht anwendbar` wird aus dem Nenner entfernt.
- Wenn Level 1 ausschließlich `Nicht anwendbar` ist, ergibt die Dimension `NaN`.
- Die Berechnung bricht beim ersten nicht vollständig erfüllten Level ab.
- Der Reifegrad wird auf 0,25-Schritte abgerundet.

Aggregierte Durchschnittswerte werden in `core/maturity.py` berechnet.

## Ziel-Reifegrade

Die Zielauswahl wird in `pages/01_Erhebung.py` definiert.

Interne Zieloptionen:

```text
Eigenes Ziel
Optimiert
Quantitativ gemanagt
Definiert
Gemanagt
```

Mapping auf numerische Zielwerte:

```text
Gemanagt                 -> 2.0
Definiert                -> 3.0
Quantitativ gemanagt     -> 4.0
Optimiert                -> 5.0
```

`Eigenes Ziel` aktiviert eigene Zielwerte je Dimension. Diese können in der App gesetzt oder als JSON/CSV importiert werden.

## Eigene Zielwerte importieren

Die Erhebung unterstützt den Import eigener Zielwerte als JSON oder CSV.

JSON kann entweder direkt ein Objekt aus Dimensionscodes und Zielwerten sein oder ein Objekt mit dem Schlüssel `targets`.

Minimalbeispiel:

```json
{
  "targets": {
    "TD1.1": 3,
    "OG1.1": 4
  }
}
```

CSV-Dateien müssen Spalten für Code und Zielwert enthalten. Erkannte Spaltennamen sind aus dem Code belegt:

- Code-Spalte: `code`, `kürzel`, `kuerzel`, `subdimension_code`
- Zielwert-Spalte: `target`, `ziel`, `eigenes ziel`, `eigenes_ziel`, `eigenesziel`

Beispiel:

```csv
code,target
TD1.1,3
OG1.1,4
```

Zielwerte werden auf ganze Zahlen gerundet und auf den Bereich `1` bis `5` begrenzt.

## Metadaten-Dateien

Die Dateien `data/niro_td_meta.json` und `data/niro_td_meta_en.json` enthalten Metadaten für Start- und Einführungsseiten.

Vorhandene Felder:

```text
title
version
last_change
time_required
created_by
created_by_email
credit
credit_email
```

Diese Dateien sind unabhängig vom eigentlichen Reifegradmodell.

## Glossar

Das Glossar liegt im jeweiligen Modell unter `glossary`. Die Glossarseite und die Erhebungsseite verwenden diese Einträge für Begriffe, Definitionen und Verlinkungen.

Begriffe können URLs enthalten. Die Glossarseite erkennt einfache `http://`, `https://` und `www.`-Links und rendert sie als anklickbare Links.

## Maßnahmen-Datei

Maßnahmenvorschläge liegen in `data/measures.json`. Die Datei ordnet Dimensionscodes deutsch- und englischsprachige Listen zu.

Empfohlene Struktur:

```json
{
  "TD1.1": {
    "de": [],
    "en": []
  }
}
```

Der aktuelle Code normalisiert beim Laden auch ältere Listenformate, die empfohlene und im Repository vorhandene Struktur ist aber ein Objekt mit `de` und `en`.

## Priorisierung

Die Priorisierungsseite verwendet diese internen Prioritätswerte:

```text
A (hoch)
B (mittel)
C (niedrig)
```

Die leere Auswahl `""` steht für keine ausgewählte Priorität.

Die Anzeige der Prioritäten wird in `core/i18n.py` übersetzt.

## Optionale GitHub-Integration für Maßnahmen

Die Priorisierung kann neue Maßnahmen als GitHub-Issue erstellen. Dafür werden in `pages/03_Priorisierung.py` diese Streamlit-Secrets erwartet:

```toml
GITHUB_OWNER = "..."
GITHUB_REPO = "..."
GITHUB_TOKEN = "..."
```

Wie der Fine-grained Personal Access Token erstellt und in Streamlit hinterlegt wird, steht in der [Deployment-Dokumentation](DEPLOYMENT.md#github-token-einrichten).

Das erstellte Issue erhält das Label `measure:pending`.

Der Issue-Body muss zu `scripts/process_measure_issue.py` passen und enthält diese Abschnitte:

```text
### measure_text
...

### dimension_code
TD1.1

### language
de
```

Der GitHub-Actions-Workflow `.github/workflows/process-measure-issues.yml` verarbeitet solche Issues, aktualisiert bei Bedarf `data/measures.json`, committet die Änderung und schließt das Issue.

## Streamlit-Konfiguration

Die Datei `.streamlit/config.toml` enthält aktuell:

```toml
[client]
showSidebarNavigation = false

[theme]
primaryColor = "#84B819"
```

Die eingebaute Streamlit-Seitennavigation ist deaktiviert. Die App rendert ihre Navigation selbst in `app.py`.

## Branding, Farben und Bilder

Branding-Assets liegen unter `images/`.

Vorhandene Bilddateien:

```text
BVL_Logo.png
IGF-RGB.png
IPS-Logo-RGB.png
NIRO.png
bmwi.png
logo_unidoku.png
tu.png
```

Farben und Seitenlayout werden nicht zentral über eine externe Konfigurationsdatei gesteuert, sondern in Python/CSS-Blöcken innerhalb von `app.py` und den Dateien unter `pages/`.

Wichtige Farbnamen und Konstanten kommen mehrfach vor, unter anderem:

- `TU_GREEN`
- `TU_ORANGE`
- `TD_BLUE`
- `OG_ORANGE`

Änderungen am visuellen Erscheinungsbild sollten daher mit einem lokalen Streamlit-Start in mehreren Seiten geprüft werden.

## Persistenz und Snapshot-Speicher

Die App verwendet `st.session_state` und zusätzlich serverseitige Snapshot-Dateien aus `core/persist.py`.

Standardverhalten:

- Snapshot-Verzeichnis: temporäres Systemverzeichnis plus `rgm_state`
- überschreibbar über: `RGM_STATE_DIR`
- Snapshot-Dateien enthalten unter anderem Antworten, Metadaten, Zielwerte, Prioritäten, Sprache und Navigationsstatus

Diese Datenhaltung ist für lokale Entwicklung praktisch, muss bei produktiver Bereitstellung aber bewusst bewertet werden.

## JSON-Dateien prüfen

Nach Änderungen an JSON-Dateien sollte mindestens geprüft werden, ob alle JSON-Dateien lesbar sind:

```bash
python -c "import json, pathlib; [json.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('data').rglob('*.json')]; print('JSON OK')"
```

Zusätzlich sollte die App lokal gestartet werden:

```bash
python -m streamlit run app.py
```

## Hinweise für Änderungen

- Bestehende Dimensionscodes und Frage-IDs möglichst stabil halten.
- Deutsche und englische Modell-Datei parallel pflegen.
- UI-Übersetzungen in `core/i18n.py` in beiden Sprachen ergänzen.
- Antwortoptionen nicht isoliert ändern, weil Scoring und Anzeige davon abhängen.
- `data/measures.json` nur mit gültigen Dimensionscodes pflegen.
- Keine Secrets in das Repository committen.
