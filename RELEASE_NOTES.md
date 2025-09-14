# VekBase Increment Release Notes (Draft)

Date: 2025-09-14

## Scope
This draft summarizes the latest development increments implemented since the previous baseline (post analytics & queue enhancements). It is intended for internal review prior to tagging a release.

## Added
1. Extended Simulation Parameters
   - `run_sim` now supports `take_profit_pct`, `stop_loss_pct`, and `fee_rate_pct`.
   - Backward compatible (hash unchanged when new params omitted).
   - New tests: deterministic TP/SL + fee behavior & backward compatibility hash check.

2. Snapshot Coverage Expansion
   - New snapshot targets: `sim_equity_curve`, `benchmark_overlay_sample`.
   - Deterministic synthetic data for stable baselines.
   - Tests ensure baseline create + no-diff flows.

3. Retrieval Relevance Heuristic
   - Added `compute_relevance` scoring with boosts (title + markdown headings).
   - `retrieve` accepts `advanced` flag (or env `VEK_RETRIEVAL_ADV=1`).
   - New test verifies advanced scoring monotonicity.

4. UI Smoke Test Coverage
   - Added `test_ui_smoke.py` exercising retrieval (basic vs advanced) and decision card lifecycle in a temp workspace.

5. Risk Metrics (Feature Flagged)
   - Added historical VaR (95%, 99%) and worst trade return / PnL metrics under env flag `VEK_RISK_METRICS=1`.
   - Computed via empirical quantiles on realized trade returns.
   - Tests ensure metrics appear only when flag set.

6. Console Dark Mode
   - Introduced theming helper (`ui/console_theme.py`) applying dark palette to Altair charts when `VEK_CONSOLE_DARK=1`.
   - Separate tests verify background/foreground style adjustments.

7. Embedding Retrieval Experiment
   - Deterministic pseudo-embedding (hashed bigrams -> fixed vector) with cosine similarity ranking behind `VEK_RETRIEVAL_EMB=1` or `retrieve(..., embedding=True)`.
   - Falls back to advanced relevance when embeddings disabled.
   - Tests cover ranking determinism and mode selection.

8. Decision Card Action Validation
   - Strengthened `ActionSpec.validate()` rules:
       * `type` ∈ {hold, add, trim, exit}
       * `target_w` required for add/trim; optional for hold; must be omitted or 0 for exit.
       * `target_w` (if provided) ≥ 0.
       * `ttl_days` (if provided) ≥ 1.
   - New negative tests for each invalid scenario plus positive hold-without-target case.

9. Decision Card Workflow
   - Added fields: `status` (draft|proposed|approved|rejected), `reviewers`, `approved_at`, `expires_at`.
   - Transition helper `transition_status(card, new_status, reviewer, now)` enforcing:
      * draft -> proposed
      * proposed -> approved | rejected
      * Idempotent same-status calls allowed
   - On approval: sets `approved_at` and computes `expires_at = approved_at + ttl_days` when action has `ttl_days`.
   - Tests cover valid & invalid transitions and expiry computation.

10. Extended Risk Metrics
   - Added Expected Shortfall (`es_95`, `es_99`) and rolling historical VaR(95) series (`rolling_var95_series`) behind `VEK_RISK_METRICS` flag.
   - Rolling series computed over prefix windows (window=20) for potential UI charting.
   - Tests verify presence when flag on and absence when off.

## Improved
 - Minor internal docstrings & code comments for simulation module.
 - Hash input updated to incorporate new sim params.

## Fixed
 - `retrieval` snippet UnboundLocalError introduced during heuristic addition (covered by tests).

## Test Suite
 - Total tests: 96 passing.
 - New tests added since baseline: simulation TP/SL/fee, snapshot targets, retrieval advanced, UI smoke, risk metrics (flag on/off), console theme, embedding retrieval, action validation edge cases, decision card workflow, extended risk metrics (ES & rolling VaR).

## Environment Flags
 - Retrieval:
    * `VEK_RETRIEVAL_ADV=1` advanced heuristic boosts.
    * `VEK_RETRIEVAL_EMB=1` pseudo-embedding cosine mode.
 - Analytics Risk: `VEK_RISK_METRICS=1` enables VaR & adverse metrics.
 - Console Theme: `VEK_CONSOLE_DARK=1` activates dark chart styling.
 - (Existing) `VEK_DEFAULT_DATA`, `VEK_ADMIN_DEVTOOLS` unchanged.

## Backward Compatibility
 - Simulation: Existing callers unaffected when omitting new params.
 - Retrieval: Baseline ranking unchanged unless advanced or embedding flags enabled.
 - Decision Cards: Existing cards without stricter action fields remain valid (rules only constrain new/updated actions). Exit actions with non-zero `target_w` must be normalized before save.
 - Snapshots: New targets additive; existing baselines untouched.

## Next (Proposed)
 - Decision card audit trail (transition history log) & reviewer role enforcement.
 - Embedding vector caching & hybrid (BM25-style + embedding) scoring.
 - Additional risk metrics: Expected Shortfall rolling series, drawdown-based stress scenarios.
 - Chart interactivity enhancements (tooltip richer metrics, dark/light auto-switch).

## Changelog Format TODO
 - Prior to release, reformat into semantic version section (e.g. `## [0.x.y] - YYYY-MM-DD`).
 - Add commit references once consolidated.

---
Draft generated via automated assistant; review & adjust narrative tone as needed before publishing.
