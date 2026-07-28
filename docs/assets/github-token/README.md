# Screenshots: GitHub-Token einrichten

Diese Bilder gehören zur Anleitung in `docs/DEPLOYMENT.md` im Abschnitt `GitHub-Token einrichten`.

Wichtig: GitHub-Token sind mit Passwörtern vergleichbar. Auf Screenshots darf niemals ein echter Token sichtbar sein.
Sichtbare Token-Werte müssen vor dem Commit vollständig geschwärzt werden.

| Datei | Inhalt |
| --- | --- |
| `1.png` | GitHub-Profilmenü öffnen und `Settings` auswählen |
| `2.png` | In den GitHub-Einstellungen `Credentials` öffnen; alternativ `Developer settings` nutzen |
| `3.png` | `Fine-grained personal access tokens` beziehungsweise `Fine-grained tokens` auswählen |
| `4.png` | Auf der Token-Übersicht `Generate new token` starten |
| `5.png` | Token-Name, Beschreibung, Resource owner, Expiration und Repository-Zugriff festlegen |
| `6.png` | `Only select repositories` wählen und `aldebsmouaiad/unidoku` auswählen |
| `7.png` | Unter `Permissions` die Repository-Berechtigung `Issues` hinzufügen |
| `8.png` | Für `Issues` die Berechtigung `Read and write` auswählen |
| `9.png` | Fertige Berechtigung kontrollieren und `Generate token` klicken |
| `10.png` | GitHub-Bestätigung für die Token-Erstellung bestätigen |
| `11.png` | Erzeugten Token sofort kopieren, Token-Wert ist geschwärzt |
| `12.png` | In Streamlit Community Cloud die App-Einstellungen öffnen |
| `13.png` | In den App-Einstellungen den Bereich `Secrets` öffnen |
| `14.png` | `GITHUB_OWNER`, `GITHUB_REPO` und `GITHUB_TOKEN` als Secrets speichern |
