# Copilot Working Agreements

When editing:
- Respektiere Datei-Header (Context Banner).
- Modifiziere nur, was zur Aufgabe gehört.
- Schreib Tests, wenn Kernlogik betroffen ist.
- Erhalte Schnittstellen (`core/*`), füge keine stillen Abhängigkeiten hinzu.
- Keine Hidden I/O in Analytics/Sim.
 - Pfadprobleme werden über `pytest.ini` gelöst, keine sys.path Hacks.
 - Kontextdateien regelmäßig synchronisieren (heute: realized-only Metrics, keine RAG Module vorhanden).
