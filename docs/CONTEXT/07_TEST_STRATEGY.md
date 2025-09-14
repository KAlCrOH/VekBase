# Test Strategy (Aktualisiert)

## Current Test Layers
1. Unit
	- Analytics core: realized PnL, drawdown, holding duration, CAGR.
	- Risk metrics: VaR, ES, rolling VaR (flag on/off behavior).
	- Retrieval: basic vs advanced vs embedding ranking determinism.
	- DecisionCard: action validation edge cases + workflow transitions.
2. Integration / Smoke
	- UI smoke (retrieval modes + decision card lifecycle).
	- Simulation with extended params (TP/SL/Fee) deterministic hash & persistence path.
	- Snapshots: new targets (simulation equity, benchmark overlay) baseline creation.
3. Feature Flag Isolation
	- Each flagged feature tested both active & inactive to confirm non-intrusion.
4. Determinism / Idempotency
	- Repeated runs of embedding retrieval produce identical orderings.
	- Simulation with same seed & params yields stable hash.

## Coverage Summary
- Total Tests: 96 (passing).
- Dark Mode: separate assertions on chart config differences (non-visual structural checks).
- Extended Risk: ES & rolling VaR series length / presence validated.
- Workflow: transition invalid path negative tests.

## Planned Additions (Next Increments)
| Area | Planned Tests |
|------|---------------|
| Strategy Batch Runner | Param grid cardinality, seed reproducibility, robustness metric calculation |
| Regime Detection | Synthetic labeled series match accuracy, short-series fallback |
| Factor Attribution | Synthetic beta recovery within tolerance, alpha ~0 for pure factor |
| Portfolio Optimizer | Diversification benefit (uncorrelated vs correlated), marginal contribution non-negative sum consistency |
| Failure Pattern Miner | Cluster recovery on synthetic features, empty-loss graceful output |
| Retrieval Filters | (ticker, as_of) exclusion of future docs |
| Snapshot Fuzz | Numeric tolerance harness for minor float drift |
| Audit Trail | Future: recorded transitions length increments correctly |

## Tooling & Process
- Pytest markers (future) for flag-dependent suites (`@pytest.mark.flag('VEK_RISK_METRICS')`).
- Potential snapshot numeric diff helper (epsilon-based) for rolling risk series.

## Risk Mitigation
- Flag gating reduces regression surface when feature off.
- Deterministic pseudo-embeddings avoid flaky similarity order.

## Open Items
- Regime, Attribution, Portfolio, Failure Miner tests (await implementation).
- Snapshot regression for new risk/rolling metrics (decide on stable fixture subset).
- Retrieval filter enforcement tests (blocked pending implementation).

Referenz: Roadmap Tabelle (I1–I5) für zeitliche Priorisierung.
