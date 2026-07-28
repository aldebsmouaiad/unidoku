# Installation

Diese Anleitung beschreibt, wie das Reifegradmodell-Projekt lokal installiert, gestartet, gestoppt und aktualisiert wird. Die Befehle beziehen sich auf die tatsächliche Projektstruktur dieses Repositorys.

## Überblick

- Repository: `https://github.com/aldebsmouaiad/unidoku.git`
- Streamlit-Einstiegspunkt: `app.py`
- Python-Abhängigkeiten: `requirements.txt`
- optionale Linux-Systempakete: `packages.txt`
- Streamlit-Konfiguration: `.streamlit/config.toml`
- empfohlene Python-Version: Python 3.11

Das Projekt enthält kein `pyproject.toml`, kein `setup.py` und keine Paketinstallation über `pip install .`. Die Anwendung wird direkt mit Streamlit gestartet.

## Voraussetzungen

Benötigt werden:

- Git
- Python 3.11
- eine Shell, zum Beispiel Windows PowerShell, macOS Terminal oder eine Linux-Shell
- Internetzugang zum Klonen des Repositorys und Installieren der Python-Pakete

Unter Linux können für Plotly/Kaleido und PDF-/Bildexporte zusätzliche Systembibliotheken erforderlich sein. Die im Repository vorgesehenen Pakete stehen in `packages.txt`.

## Python-Version prüfen

### Windows PowerShell

```powershell
py -3.11 --version
```

Falls mehrere Python-Versionen installiert sind:

```powershell
py -0p
```

### macOS/Linux

```bash
python3.11 --version
```

Falls `python3.11` nicht vorhanden ist, prüfen:

```bash
python3 --version
```

Empfohlen ist Python 3.11, weil die Devcontainer-Konfiguration und der GitHub-Actions-Workflow diese Version verwenden.

## Repository klonen

```bash
git clone https://github.com/aldebsmouaiad/unidoku.git
cd unidoku
```

## Installation unter Windows PowerShell

Virtuelle Umgebung erstellen:

```powershell
py -3.11 -m venv .venv
```

Virtuelle Umgebung aktivieren:

```powershell
.\.venv\Scripts\Activate.ps1
```

Falls PowerShell die Aktivierung blockiert, kann die Ausführungsrichtlinie nur für die aktuelle PowerShell-Sitzung gelockert werden:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Pip aktualisieren und Abhängigkeiten installieren:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Streamlit-App starten:

```powershell
python -m streamlit run app.py
```

Nach dem Start zeigt Streamlit eine lokale URL an, normalerweise:

```text
http://localhost:8501
```

## Installation unter macOS/Linux

Virtuelle Umgebung erstellen:

```bash
python3.11 -m venv .venv
```

Falls `python3.11` auf dem System nicht verfügbar ist, kann stattdessen die vorhandene Python-3-Installation verwendet werden, sofern sie kompatibel ist:

```bash
python3 -m venv .venv
```

Virtuelle Umgebung aktivieren:

```bash
source .venv/bin/activate
```

Pip aktualisieren und Abhängigkeiten installieren:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Streamlit-App starten:

```bash
python -m streamlit run app.py
```

Nach dem Start zeigt Streamlit eine lokale URL an, normalerweise:

```text
http://localhost:8501
```

## Zusätzliche Systempakete unter Debian/Ubuntu

Für browserbasierte Exporte mit Kaleido können unter Debian/Ubuntu zusätzliche Systempakete nötig sein. Das Repository enthält dafür `packages.txt`.

Installation:

```bash
sudo apt update
sudo xargs apt install -y < packages.txt
```

Dieser Schritt ist vor allem für Linux-Server, Container, Codespaces oder Streamlit-Deployments relevant. Unter Windows und macOS ist er normalerweise nicht erforderlich.

## Anwendung stoppen

Im Terminal, in dem Streamlit läuft:

```text
Ctrl+C
```

Falls der Prozess im Hintergrund läuft, muss er über die Prozessverwaltung des Betriebssystems beendet werden.

## Anwendung auf anderem Port starten

Wenn Port `8501` bereits belegt ist:

```bash
python -m streamlit run app.py --server.port 8502
```

Die App ist dann normalerweise unter folgender Adresse erreichbar:

```text
http://localhost:8502
```

## Lokale Installation aktualisieren

Im Projektordner:

```bash
git pull
python -m pip install -r requirements.txt
```

Wenn Streamlit bereits läuft, die Anwendung danach stoppen und neu starten.

## Devcontainer und Codespaces

Das Repository enthält `.devcontainer/devcontainer.json`. Die Konfiguration verwendet ein Python-3.11-Devcontainer-Image und installiert beim Start Inhalte aus `packages.txt` und `requirements.txt`.

Der Devcontainer startet die Anwendung mit folgendem Befehl:

```bash
streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false
```

Port `8501` ist im Devcontainer als Anwendungsport vorgesehen.

## Minimale Funktionsprüfung

Nach der Installation kann ein Syntax-/Compile-Check ausgeführt werden:

```bash
python -m compileall -q app.py core pages scripts
```

Danach die Anwendung starten:

```bash
python -m streamlit run app.py
```

Wenn Streamlit ohne Fehler startet und eine lokale URL ausgibt, ist die Grundinstallation erfolgreich.

## Typische Fehler

### `py` wird unter Windows nicht gefunden

Python ist nicht installiert oder der Python Launcher ist nicht verfügbar. Python 3.11 installieren und danach ein neues PowerShell-Fenster öffnen.

### `python3.11` wird unter macOS/Linux nicht gefunden

Python 3.11 ist nicht installiert oder nicht unter diesem Namen verfügbar. Prüfen:

```bash
python3 --version
```

Falls die vorhandene Version kompatibel ist, kann die virtuelle Umgebung mit `python3 -m venv .venv` erstellt werden.

### Aktivierung der virtuellen Umgebung ist unter PowerShell blockiert

Für die aktuelle Sitzung:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Paketinstallation schlägt fehl

Pip aktualisieren und die Installation erneut ausführen:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Streamlit meldet, dass Port `8501` belegt ist

Einen anderen Port verwenden:

```bash
python -m streamlit run app.py --server.port 8502
```

### PDF- oder Diagrammexport funktioniert unter Linux nicht

Die Systempakete aus `packages.txt` installieren:

```bash
sudo apt update
sudo xargs apt install -y < packages.txt
```

### GitHub-Issue-Erstellung funktioniert nicht

Die normale lokale Erhebung funktioniert auch ohne GitHub-Secrets. Für das automatische Erstellen von GitHub-Issues über die Priorisierung müssen in der Streamlit-Umgebung folgende Secrets gesetzt sein:

- `GITHUB_OWNER`
- `GITHUB_REPO`
- `GITHUB_TOKEN`

Die genaue Einrichtung des Fine-grained Personal Access Tokens ist in [DEPLOYMENT.md](DEPLOYMENT.md#github-token-einrichten) beschrieben.

## Hinweise zu lokalen Dateien

Die virtuelle Umgebung `.venv/`, Python-Cache-Dateien und `.streamlit/secrets.toml` sind durch `.gitignore` vom Commit ausgeschlossen.

Die App kann serverseitige Snapshot-Dateien im temporären Verzeichnis des Systems speichern. Der Speicherort kann über `RGM_STATE_DIR` angepasst werden.
