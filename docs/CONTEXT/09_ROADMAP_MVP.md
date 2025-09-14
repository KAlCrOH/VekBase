# Roadmap (MVP → Research Workbench Evolution)

## Delivered (Baseline -> Current)
Implemented across prior increments (chronologisch):
1. Core Foundations: Charter, trade schema, simple simulation, realized analytics (PnL, CAGR, drawdown), DevTools queue, snapshots.
2. Extended Simulation: TP/SL/Fee parameters (backward compatible hashing).
3. Retrieval Enhancements: Advanced heuristic scoring + pseudo-embedding experiment (flag gated).
4. Risk Metrics: VaR(95/99), worst trade stats; later Extended Risk: ES95/ES99 & rolling VaR(95) series.
5. Decision Cards: Action spec (validated) + Workflow (status, reviewers, approval expiry).
6. UI Enhancements: Dark mode theming, multi-series equity overlays, admin smoke tests.
7. Snapshot Coverage Expansion: Simulation equity & benchmark overlay.

## Current Strategic Theme
Shift from single-path analytics to comparative & robustness research: parameter sweeps, regime conditioning, factor attribution, portfolio assembly, and failure mining.

## Upcoming Increments (Top 5 High Leverage)
| ID | Increment | Goal | Status | Flag | Core Outputs |
|----|-----------|------|--------|------|--------------|
| I1 | Strategy Batch Runner & Param Sweep | Evaluate tactic families & robustness | Implemented (core API & tests) | `VEK_STRAT_SWEEP` (not yet gating) | Batch results list, summary (robust_cagr_median/p05/p95, failure_rate, param_sensitivity_score) |
| I2 | Market Regime Detection | Condition performance on environment | Implemented (labeling + summaries) | `VEK_REGIME` (not yet gating) | Regime labels, per-regime return summary |
| I3 | Factor Attribution Layer | Separate factor beta vs residual alpha | Implemented (core OLS) | `VEK_ATTRIBUTION` (not gating) | Betas, alpha proxies, R², factor contributions |
| I4 | Portfolio Allocation Optimizer | Capital deployment across strategies | Implemented (core policies) | `VEK_PORTFOLIO` (not gating) | Portfolio equity, weights, diversification benefit |
| I5 | Failure Pattern Miner | Cluster & explain losing patterns | Implemented (deterministic core) | `VEK_FAILURE_MINER` (not gating) | Loss clusters, summaries, avoidance heuristic |

## Increment Details & Acceptance Criteria
### I1 Strategy Batch Runner
Status: Implemented (module `app/research/strategy_batch.py`) with two exemplar strategies (`ma_crossover`, `random_flip`).
Contract: `run_strategy_batch(strategies, price_series, param_grid, seeds, failure_dd_threshold=0.3) -> (results, summary)`.
Results List Entries: `{strategy, param_hash, params, seed, metrics:{cagr, max_drawdown_realized}}`.
Summary Fields:
	- `robust_cagr_median`: 50th percentile of per-run CAGR.
	- `robust_cagr_p05` / `robust_cagr_p95`: 5th / 95th percentile dispersion band.
	- `failure_rate`: Share of runs where `max_drawdown_realized > failure_dd_threshold`.
	- `param_sensitivity_score`: sqrt(variance of group means (CAGR per unique param combination) vs global mean; 0 if only one combo).
	- `runs`: total executed runs (= strategies * param combinations * seeds).
	- `param_combinations`: size of cartesian parameter grid.
Determinism: Fully deterministic given `price_series`, param set, and `seed` (CAGR values sanitized to finite range).
Tests: Added `tests/test_strategy_batch.py` covering determinism, run count, quantile correctness, param sensitivity, single-combo edge, empty strategy list.
Deferred (Next): Feature flag enforcement (`VEK_STRAT_SWEEP`), richer strategies, optional Sharpe proxy, snapshot integration.

### I2 Market Regime Detection
Status: Implemented (module `app/research/regime_detection.py`).
Regime Dimensions: rolling volatility quantile band (low/mid/high) + trend slope bucket (down/flat/up).
Artifacts:
	- `compute_regime_labels` -> list[{idx, price, vol, vol_bucket, trend_slope, trend_bucket}]
	- `summarize_regime_returns` -> per (vol_bucket, trend_bucket) realized return aggregation.
Tests: Synthetic steady trend (majority up), mixed volatility phases (distribution across low/high), equity increment mapping, empty input resilience.
Deferred (Next): Exposure share metrics, regime flip counts, optional visualization hooks, feature flag gating.

### I3 Factor Attribution Layer
Status: Implemented (module `app/research/factor_attribution.py`).
Process: per-period returns from equity curve -> OLS (pseudo-inverse with ridge) vs factor matrix.
Outputs: `betas` (dict factor->beta), `alpha_mean`, `alpha_cagr_proxy`, `r_squared`, `residual_std`, `factor_contributions` (normalized |beta * mean_factor|).
Tests: single-factor recovery (noise-free), zero-return series, collinearity stability (duplicate factors), insufficient data edge.
Deferred: Multi-period frequency awareness (dynamic periods_per_year), residual distribution diagnostics, per-regime factor attribution integration.

### I4 Portfolio Allocation Optimizer
Status: Implemented (module `app/research/portfolio_optimizer.py`).
Inputs: Multiple realized equity curves (or trade-derived curves) aligned via timestamp intersection.
Implemented Allocation Policies:
	- `equal_weight`: uniform 1/N allocation.
	- `vol_parity`: weights ∝ 1/σ (normalized inverse volatility).
	- `max_dd_capped`: scales vol_parity weights if provisional portfolio max drawdown exceeds cap (retains potential uninvested cash).
Outputs / Metrics:
	- `portfolio_cagr`: total compounded return (non-annualized) over period.
	- `portfolio_max_dd`: peak-to-trough drawdown.
	- `diversification_benefit`: (Σ w_i σ_i / σ_port) - 1 (≈0 when series perfectly correlated / identical).
	- `weight_sum`: sum of final weights (<=1 if capped scaling).
Tests: alignment accuracy, vol parity inverse-vol weighting, drawdown cap scaling, zero diversification for identical streams, general metric sanity.
Deferred: correlation-aware optimization, turnover & transaction cost metrics, Kelly fraction, regime-aware rebalancing, union alignment w/ fill, contribution decomposition.

### I5 Failure Pattern Miner
Status: Implemented (module `app/research/failure_pattern_miner.py`).
Pipeline: loss trade filtering -> feature vector extraction (pct_loss, magnitude_abs, placeholder_duration, side_indicator, time_index_norm) -> deterministic farthest-first seeding + refinement clustering -> cluster summarization.
Outputs:
	- `loss_clusters`: list of clusters with centroid feature vector, cluster size, mean loss, representative raw feature stats.
	- `avoidable_loss_estimate`: heuristic = sum of (cluster mean loss * cluster size) for clusters whose mean pct_loss exceeds global mean pct_loss (proxy for systematic avoidable patterns).
Determinism: Farthest-first centroid initialization ordering is stable (no RNG); refinement loops fixed iteration count.
Tests: synthetic two-cluster separation, no-loss edge (empty outputs, estimate 0), single-loss edge (single cluster), determinism (re-run identical result), size >= k guard.
Deferred: Real holding duration feature, richer temporal/contextual features (e.g., time-of-day, regime tag join), narrative generation, gating flag activation, distance metric experimentation (Mahalanobis), cluster drift over time.

## Feature Flags (Current & Planned)
| Flag | Purpose | Status |
|------|---------|--------|
| `VEK_RISK_METRICS` | VaR, ES, rolling VaR metrics | Implemented |
| `VEK_CONSOLE_DARK` | Dark mode theming | Implemented |
| `VEK_RETRIEVAL_ADV` | Advanced relevance scoring | Implemented |
| `VEK_RETRIEVAL_EMB` | Pseudo-embedding retrieval | Implemented |
| `VEK_DECISIONCARDS` | (Future gating if needed) decision card UI features | Placeholder |
| `VEK_STRAT_SWEEP` | Strategy batch runner | Planned |
| `VEK_REGIME` | Regime detection | Planned |
| `VEK_ATTRIBUTION` | Factor attribution | Planned |
| `VEK_PORTFOLIO` | Portfolio optimizer | Planned |
| `VEK_FAILURE_MINER` | Failure pattern mining | Planned |

## Technical Debt / Follow-Ups
- Centralize flag lookup (reduce scattered `os.getenv`).
- Snapshot numeric tolerance layer for new floating metrics.
- Optional embedding vector cache (hash-based) once real models considered.
- DecisionCard audit trail (transition history).

## Out-of-Scope (Near Term)
- Live market data streaming (placeholder until strategy diversity proven).
- LLM-based narrative generation (after Failure Miner establishes structured outputs).

## Backlog Reference
Legacy backlog now partially superseded; authoritative future work captured above. Historic list retained in `docs/DOCUMENTATION/tmp_backlogCollection.md` for traceability.

