# Reifegradmodell Technische Dokumentation

Streamlit-Anwendung zur Erhebung, Auswertung und Weiterentwicklung des Reifegrads in der Technischen Dokumentation.
Die App führt durch einen fragebasierten Erhebungsprozess, visualisiert Ergebnisse, unterstützt die Priorisierung
von Maßnahmen und bietet Exporte für die Weiterverarbeitung.

## Projektstatus

Das Repository enthält eine lauffähige Streamlit-App mit deutschem und englischem Datenmodell.
Die wichtigsten Projekt-, Installations-, Konfigurations-, Deployment- und Entwicklungsinformationen sind dokumentiert.
Automatisierte Tests sind derzeit noch nicht vorhanden. Das Projekt steht unter der MIT-Lizenz.

## Ziel und Einsatzgebiet

Die Anwendung richtet sich an Organisationen, Teams und Fachbereiche, die den aktuellen Reifegrad ihrer Technischen
Dokumentation strukturiert erfassen und Verbesserungsmaßnahmen ableiten möchten. Das vorhandene Datenmodell
unterscheidet zwischen Dimensionen der Technischen Dokumentation und organisatorischen Einflussfaktoren.

## Wichtigste Funktionen

- mehrseitige Streamlit-Oberfläche mit Start, Einführung, Ausfüllhinweisen, Erhebung, Dashboard, Priorisierung, Glossar und Gesamtübersicht
- deutsch- und englischsprachige Modell- und UI-Texte
- fragebasierte Erhebung mit Antwortskala und Reifegradberechnung
- eigene Ziel-Reifegrade je Dimension
- Import und Export von Zwischenständen als JSON
- Ergebnisübersichten mit Tabellen und Radar-Diagrammen
- CSV-Export für Ergebnistabellen
- PDF-Export der Gesamtübersicht
- Priorisierung und optionale Übermittlung neuer Maßnahmen als GitHub-Issue
- Glossar mit Rücksprung zur Erhebung

## Technischer Überblick

- Sprache: Python
- Framework: Streamlit
- Datenverarbeitung: pandas
- Diagramme: Plotly
- Bildexport für Diagramme: Kaleido
- PDF-Erzeugung: ReportLab
- Konfiguration und Inhalte: JSON-Dateien unter `data/`
- Streamlit-Konfiguration: `.streamlit/config.toml`
- GitHub-Automatisierung: `.github/workflows/process-measure-issues.yml`

Der Streamlit-Einstiegspunkt ist `app.py`.

## Voraussetzungen

Empfohlen wird Python 3.11, da Devcontainer und GitHub Actions diese Version verwenden. Die benötigten Python-Pakete stehen in `requirements.txt`.

Für den PDF- beziehungsweise Plotly/Kaleido-Export können unter Linux zusätzliche Systempakete erforderlich sein. Die im Repository vorgesehenen Pakete stehen in `packages.txt`.

## Schnellstart

### Windows PowerShell

```powershell
git clone https://github.com/aldebsmouaiad/unidoku.git
cd unidoku
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### macOS/Linux

```bash
git clone https://github.com/aldebsmouaiad/unidoku.git
cd unidoku
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit zeigt nach dem Start eine lokale URL an, normalerweise `http://localhost:8501`.

Zum Stoppen der Anwendung im Terminal `Ctrl+C` drücken.

## Lokale Installation aktualisieren

```bash
git pull
python -m pip install -r requirements.txt
```

Wenn die Anwendung bereits läuft, danach Streamlit stoppen und neu starten.

## Grundlegende Bedienung

1. App starten und Sprache sowie Darstellung wählen.
2. Hinweise und Einführung lesen.
3. In der Erhebung Metadaten eintragen.
4. Ziel-Reifegrad festlegen oder eigene Zielwerte importieren.
5. Fragen je Dimension beantworten.
6. Dashboard und Gesamtübersicht prüfen.
7. Maßnahmen priorisieren.
8. Ergebnisse als JSON, CSV oder PDF exportieren.

## Konfiguration des Reifegradmodells

Die fachlichen Inhalte liegen in JSON-Dateien:

- `data/models/niro_td_model.json`
- `data/models/niro_td_model_en.json`
- `data/niro_td_meta.json`
- `data/niro_td_meta_en.json`
- `data/measures.json`

Die Modell-Dateien enthalten unter anderem Name, Beschreibung, Reifegradstufen, Glossar und Dimensionen. Jede Dimension enthält Code, Name, Kategorie, Beschreibung, Zielwert, Prozessprofil, Levels und Fragen.

Die Maßnahmen-Datei `data/measures.json` ordnet Dimensionscodes deutsch- und englischsprachige Maßnahmenvorschläge zu.

Wichtig: Änderungen an den JSON-Dateien sollten immer mit einem lokalen Start der App und mindestens einem Syntaxcheck geprüft werden.

## Eingabe- und Exportformate

Unterstützte Eingaben:

- Antworten in der Streamlit-Oberfläche
- JSON-Zwischenstand für Fortsetzen oder Wiedererhebung
- JSON oder CSV für eigene Ziel-Reifegrade

Unterstützte Exporte:

- JSON-Zwischenstand
- CSV-Ergebnistabellen
- PDF-Gesamtübersicht
- PNG-Downloads der Diagramme in den Diagramm-Ansichten

## Datenschutz und Datenhaltung

Die App verwendet `st.session_state` für laufende Eingaben in der Streamlit-Sitzung. Zusätzlich speichert
`core/persist.py` serverseitige Snapshot-Dateien, damit eine Erhebung über eine Assessment-ID wiederhergestellt
werden kann.

Standardmäßig werden diese Snapshots im temporären Verzeichnis des Systems unter `rgm_state` abgelegt. Der Speicherort kann über die Umgebungsvariable `RGM_STATE_DIR` geändert werden.

Die Datei `.streamlit/secrets.toml` ist durch `.gitignore` vom Commit ausgeschlossen.

## Projektstruktur

Die folgende Struktur entspricht den Projektdateien im Repository ohne `.git/`, `.venv/` und generierte `__pycache__/`-Ordner:

```text
.
+-- .devcontainer/
|   +-- devcontainer.json
+-- .github/
|   +-- workflows/
|       +-- process-measure-issues.yml
+-- .streamlit/
|   +-- config.toml
+-- core/
|   +-- __init__.py
|   +-- charts.py
|   +-- exporter.py
|   +-- i18n.py
|   +-- maturity.py
|   +-- model_loader.py
|   +-- overview.py
|   +-- persist.py
|   +-- scoring.py
|   +-- state.py
|   +-- types.py
+-- data/
|   +-- measures.json
|   +-- niro_td_meta.json
|   +-- niro_td_meta_en.json
|   +-- models/
|       +-- niro_td_model.json
|       +-- niro_td_model_en.json
+-- docs/
|   +-- assets/
|   |   +-- github-token/
|   |       +-- 1.png
|   |       +-- 2.png
|   |       +-- 3.png
|   |       +-- 4.png
|   |       +-- 5.png
|   |       +-- 6.png
|   |       +-- 7.png
|   |       +-- 8.png
|   |       +-- 9.png
|   |       +-- 10.png
|   |       +-- 11.png
|   |       +-- 12.png
|   |       +-- 13.png
|   |       +-- 14.png
|   |       +-- README.md
|   +-- CONFIGURATION.md
|   +-- DEPLOYMENT.md
|   +-- DEVELOPMENT.md
|   +-- INSTALLATION.md
+-- images/
|   +-- BVL_Logo.png
|   +-- IGF-RGB.png
|   +-- IPS-Logo-RGB.png
|   +-- NIRO.png
|   +-- bmwi.png
|   +-- logo_unidoku.png
|   +-- tu.png
+-- pages/
|   +-- 00_Ausfuellhinweise.py
|   +-- 00_Einfuehrung.py
|   +-- 00_Start.py
|   +-- 01_Erhebung.py
|   +-- 02_Dashboard.py
|   +-- 03_Priorisierung.py
|   +-- 04_Glossar.py
|   +-- 05_Gesamtuebersicht.py
+-- scripts/
|   +-- process_measure_issue.py
+-- .gitignore
+-- LICENSE
+-- README.md
+-- app.py
+-- packages.txt
+-- requirements.txt
```

## Deployment mit Streamlit

Für Streamlit Community Cloud oder eine vergleichbare Streamlit-Umgebung sind die wichtigsten Angaben:

- Repository: dieses GitHub-Repository
- Branch: `main`
- Startdatei: `app.py`
- Python-Abhängigkeiten: `requirements.txt`
- Streamlit-Konfiguration: `.streamlit/config.toml`

Falls die GitHub-Issue-Funktion der Priorisierung genutzt werden soll, müssen folgende Secrets in der Streamlit-Umgebung gesetzt werden:

- `GITHUB_OWNER`
- `GITHUB_REPO`
- `GITHUB_TOKEN`

Die genaue Einrichtung des Fine-grained Personal Access Tokens ist in der [Deployment-Dokumentation](docs/DEPLOYMENT.md#github-token-einrichten) beschrieben.

Ohne diese Secrets kann die lokale Erhebung weiter genutzt werden; das automatische Erstellen von GitHub-Issues für Maßnahmen ist dann nicht konfiguriert.

## GitHub Actions

Das Repository enthält den Workflow `.github/workflows/process-measure-issues.yml`. Er reagiert auf neu geöffnete
Issues mit dem Label `measure:pending`, verarbeitet den Issue-Body mit `scripts/process_measure_issue.py`,
aktualisiert bei Bedarf `data/measures.json`, committet die Änderung und schließt das Issue.

Es gibt derzeit keinen allgemeinen CI-Workflow für Tests oder Linting.

## Fehlerbehebung

### Streamlit startet nicht

Prüfen, ob die virtuelle Umgebung aktiv ist und alle Pakete installiert wurden:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### PDF- oder Diagrammexport funktioniert unter Linux nicht

Die in `packages.txt` genannten Systempakete können für Kaleido/Browser-basierte Exporte erforderlich sein.

### GitHub-Issue-Erstellung funktioniert nicht

Prüfen, ob `GITHUB_OWNER`, `GITHUB_REPO` und `GITHUB_TOKEN` als Streamlit-Secrets gesetzt sind und ob der Token Issues erstellen darf.

### Zwischenstand wird nicht wie erwartet wiederhergestellt

Prüfen, ob die Assessment-ID in der URL erhalten bleibt und ob der Snapshot-Speicherort erreichbar ist. Der Speicherort kann über `RGM_STATE_DIR` konfiguriert werden.

## Weiterführende Dokumentation

Vorhanden:

- [Installationsanleitung](docs/INSTALLATION.md)
- [Konfigurationsdokumentation](docs/CONFIGURATION.md)
- [Deployment-Dokumentation](docs/DEPLOYMENT.md)
- [Entwicklungsdokumentation](docs/DEVELOPMENT.md)

## Förderhinweis / Acknowledgement

Das Projekt „UniDoku“ wird im Rahmen des Programms „Industrielle Gemeinschaftsforschung“ durch das Bundesministerium für Wirtschaft und Energie aufgrund eines Beschlusses des Deutschen Bundestages gefördert. Dieses IGF-Vorhaben 01IF23157N der Forschungsvereinigung BVL e.V., Bremen, wird am Institut für Produktionssysteme der Technischen Universität Dortmund durchgeführt.

The research project "UniDoku" is funded by the Federal Ministry of Economic Affairs and Energy as part of the "Industrial Collective Research" programme on the basis of a resolution of the German Bundestag. This IGF project 01IF23157N of the Research Association BVL e.V., Bremen, is carried out at the Institute of Production Systems at TU Dortmund University.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Details stehen in [LICENSE](LICENSE).

## Kontakt und Projektlink

- Kontakt:
    Christian Koch ([christian4.koch@tu-dortmund.de](mailto:christian4.koch@tu-dortmund.de))
    Mouaiad Aldebs ([mouaiad.aldebs@tu-dortmund.de](mailto:mouaiad.aldebs@tu-dortmund.de))
- Projektlink: [https://unidoku-ips.streamlit.app/](https://unidoku-ips.streamlit.app/)
