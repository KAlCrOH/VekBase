# Glossary
Trade: Ein Ein- oder Ausstieg mit Datum/Zeit, Stückzahl, Preis, Fees.
Position: Aggregat mehrerer Trades eines Tickers.
PnL: Realisiert oder unrealisiert, Gebühren berücksichtigt.
Realized PnL: Nur geschlossene Positionsteile (FIFO) minus Gebühren.
Max Drawdown (realized): Größter Rückgang der kumulativen realized PnL Kurve.
DecisionCard: Strukturierter Vorschlag / Governance-Artefakt mit ActionSpec & Workflow (Status, Reviewer, Expiry).
Equity Curve (realized): Zeitreihe kumulativer REALIZED PnL Werte (ohne unrealized Komponenten).
Unrealized PnL: Mark-to-Market Wert offener Lots.
VaR (Value at Risk): Quantilsbasierte Verlustschätzung (historical), hier positive Zahl für Magnitude.
ES (Expected Shortfall / CVaR): Durchschnittlicher Verlust bedingt auf das schlechteste Alpha-Quantil (tail average), positive Magnitude.
Rolling VaR: Laufende Neuberechnung des VaR über Gleitfenster oder wachsende Stichproben (hier prefix/window-basiert 95%).
Strategy Sweep (Parameter Sweep): Systematischer Batchlauf mehrerer Strategien über Parameter/Gitter & Seeds zur Robustheitsmessung.
Regime: Klassifizierter Markt-Zustand (z.B. HighVol-Trend) basierend auf Volatilität & Trendmerkmalen.
Vol Bucket: Kategorie (low/mid/high) basierend auf Rolling-Vol Quantilen.
Trend Bucket: Kategorie (down/flat/up) basierend auf Rolling-Slope und adaptivem Threshold.
Regime Return Summary: Aggregation der realisierten Equity-Inkremente nach (vol_bucket, trend_bucket).
Factor Attribution: Zerlegung von Renditen in Faktoreinflüsse (Betas) und Residual/Alpha-Komponente.
Beta (Factor Beta): Regressionskoeffizient eines Faktors in der linearen Attribution (Sensitivität).
Alpha Mean: Durchschnittlicher intercept Return pro Periode nach Herausrechnen der Faktoren.
Alpha CAGR Proxy: Annualisierte Approximation aus (1+alpha_mean)^{PeriodsPerYear}-1.
Factor Contributions: Normalisierte Gewichtung |beta * mean_factor| als Anteil an Summe aller Faktoren.
Allocation Policy: Regel zur Gewichtszuteilung zwischen Strategien (z.B. equal_weight, vol_parity, max_dd_capped).
Vol Parity: Gewichtung proportional zu 1/Volatilität einer Strategie (risiko-ausgleichend).
Max Drawdown Capped Allocation: Skalierung einer Basis-Gewichtung, um Max Drawdown eines Portfolios auf Zielschwelle zu begrenzen.
Diversification Benefit (Weighted): (Σ w_i σ_i / σ_portfolio) - 1; Maß für Volatilitätsreduktion durch Diversifikation (>0 ⇒ Diversifikationseffekt, ≈0 ⇒ keine Reduktion).
Diversification Benefit: Reduktion der Portfolio-Volatilität relativ zum Durchschnitt individueller Volatilitäten.
Failure Cluster: Gruppe verlustreicher Trades mit ähnlichen Merkmalen (zur Muster-Erkennung / Remediation).
Loss Feature Vector: Numerische Repräsentation eines Verlust-Trades (aktuell: pct_loss, abs_loss, duration_placeholder, side, time_index_norm).
Farthest-First Clustering: Deterministisches Greedy-Verfahren zur Auswahl initialer Zentren durch sukzessive Wahl des punktes mit größter Distanz zu bestehenden Zentren.
Avoidable Loss Estimate: Heuristische Schätzung aggregierter vermeidbarer Verluste (Summe cluster_mean_loss * size über "überdurchschnittliche" Verlustcluster).
Robustness Metrics: Kennzahlen zur Stabilität (z.B. Median vs P05/P95 CAGR über Parameterräume).
Param Sensitivity Score: Quadratwurzel der Varianz der CAGR-Gruppenmittelwerte (je Parameter-Kombination) relativ zum globalen Mittel; 0 falls nur eine Kombination.
Marginal Contribution: Zusätzlicher Beitrag einer Strategie zu Portfolio-Kennzahlen (z.B. PnL, Drawdown-Reduktion).
Audit Trail (DecisionCard): Geplanter Verlauf von Status-Änderungen inkl. Zeit/Reviewer.
