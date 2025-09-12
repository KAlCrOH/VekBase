# Copilot Working Agreements

1) Änderungsregeln (Editing Discipline)

Context Banner/Datei‑Header: Unverändert lassen. Änderungen nur, wenn die Aufgabe explizit „Header aktualisieren“ fordert.

Scope strikt: Modifiziere nur Dateien/Funktionen, die kausal zur Aufgabe gehören. Keine „Beifang“-Refactorings.

Schnittstellenstabilität: Öffentliche APIs und core/* sind stabil. Breaking‑Changes nur mit Migrationshinweis + Changelog‑Eintrag + Major‑Bump‑Hinweis (kein stilles Umbauen).

Keine stillen Abhängigkeiten: Jede neue Runtime‑/Build‑Abhängigkeit muss im Manifest (z. B. pyproject.toml, package.json, .csproj) sichtbar werden und in der PR‑Beschreibung begründet sein.

Determinismus: Kein verdeckter State. Randomness seeded, Caches injektionsfähig, Uhrzeit/Umgebung mockbar.

2) Tests & Qualität (Gates, nicht „Nice‑to‑have“)

Tests bei Kernlogik: Wenn Produktionslogik, Datenmodelle, Parser, Serialisierung, Sicherheits‑/Fehlerpfade oder Public API berührt werden → Pflichttests (Unit und mind. 1 Negativfall).

Coverage‑Ziel: PR darf Coverage des betroffenen Moduls nicht senken.

Statische Analysen: Linter/Analyzer dürfen nicht rot sein.

SARIF‑Artefakte: Statische Scans sollen als SARIF vorliegen und im PR angezeigt werden (GitHub Code Scanning). 
GitHub Docs
+2
GitHub Docs
+2

3) Pfade & Imports (Python / Polyglott anpassbar)

Keine sys.path‑Hacks. Pfadthemen werden über pytest.ini (z. B. testpaths, pythonpath) oder korrekte Packaging‑Metadata gelöst.

Relative Importe bevorzugen, falls Packaging nicht gegeben; sonst sauberes Paketlayout.

4) Analytics / Simulation

Keine Hidden I/O in analytics/* und sim/*: keine Netzwerk‑/Datei‑Zugriffe ohne explizite Parametrisierung.

Reproduzierbarkeit: Seeds, Parameter und Artefakte explizit; Outputs nach ./.artifacts/… (nicht ins Repo).

Laufzeitgrenzen: Simulationsjobs sollen lokal reproduzierbar sein; lange Läufe in CI opt‑in, nicht Default.

5) Kontext & Datenhoheit

Kontextdateien synchron halten. Heute gilt: „realized‑only Metrics“, keine RAG‑Module. Agenten dürfen keine RAG‑Platzhalter, verdeckte Embeddings‑Setups oder externe Wissensaufrufe hinzufügen.

Datenzugriff explizit: Jede neue Datenquelle braucht README‑Notiz (Quelle, Format, Lizenz, Aktualisierung).

6) Sicherheit & Compliance (Non‑Negotiable)

Keine Secrets im Code/Config. Push‑Protection/Secret‑Scanning muss grün sein; Verstöße blockieren. 
GitHub Docs
+2
GitHub Docs
+2

Dependency‑Changes: Jede neue/aktualisierte Abhängigkeit wird via Dependency Review Action bewertet; PR blocken bei bekannten CVEs/Lizenzen nach Policy. 
GitHub
+2
GitHub Docs
+2

Least Privilege: Neue Tokens/Scopes nur mit begründetem Minimalumfang.

Destruktive Schritte: Migrations/Deletes nur nach explizitem Opt‑in im PR‑Text („Destructive Change: APPROVED BY <Name>“).

7) Dokumentation & Developer‑Ergonomie

README/USAGE aktualisieren, wenn Build/Run/Test‑Anweisungen sich ändern.

API‑Dokumentation (Docstrings/XmlDoc/TypeDoc/DocFX) bei Publikums‑APIs pflegen.

Changelog & ADRs: Breaking‑Changes → CHANGELOG.md + kurze ADR‑Notiz (Was/Warum/Alternativen).

8) Pull Requests & Commits

PR‑Beschreibung zwingend: Problem → Ansatz → Änderungen → Risiken → Teststrategie → Migrationshinweise.

Atomic Commits: Sachlich geklammert (Code/Tests/Doku), keine „Mixed Bags“.

Labels & Owners: Betroffene Komponenten taggen; Reviewer mit fachlicher Ownership anpingen.

Keine Automerge durch Agenten. Merge bleibt menschengeführt.

9) Agent‑spezifische Leitplanken (VS Agent Mode & Coding Agent)

Bestätige Terminals: In VS Agent Mode keine Terminal‑Kommandos ohne explizite Bestätigung; Agent läuft mit gleichen Rechten wie die IDE – entsprechend vorsichtig. 
Microsoft Learn

Dateisichtbarkeit (VS): Agent sieht nur Dateien im Lösungsordner/Unterordnern; außerhalb liegende Artefakte bleiben tabu. 
Microsoft Learn

Coding‑Agent Arbeitsweise: Aufgaben können dem Copilot Coding Agent delegiert werden (z. B. aus Chat/Agents Panel); Ergebnis sind PRs, die du reviewst. Risiken/Abhilfen sind dokumentiert → Branch‑Schutz & Status‑Checks nutzen. 
GitHub Docs
+2
GitHub Docs
+2

10) Definition of Done (DoD)

Ein PR ist fertig, wenn alle Punkte grün sind:

 Linter/Analyzer laufen ohne Fehler/Warn‑Downgrade.

 Tests vorhanden/aktualisiert; Coverage unverändert oder höher.

 Keine verletzten Security‑Checks (Secret‑Scanning/Push‑Protection, Dependency‑Review, Code Scanning). 
GitHub Docs
+3
GitHub Docs
+3
GitHub Docs
+3

 README/Docs/Changelog/ADR (falls relevant) aktualisiert.

 Keine Breaking‑Changes an core/* ohne Migrationshinweis.

 PR‑Beschreibung vollständig (Problem/Ansatz/Risiken/Tests/Migration).

 „Kontextdateien synchron“ bestätigt (Stand: realized‑only Metrics, keine RAG).
