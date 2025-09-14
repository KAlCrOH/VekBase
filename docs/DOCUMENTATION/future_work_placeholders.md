# Future Work Placeholders (Schemas & Notes)

## Strategy Batch Runner (I1)
Planned Data Artifacts:
- batch_run_manifest.json
  {
    "run_id": str,
    "created_at": iso8601,
    "strategies": ["ma_crossover", "random_flip"],
    "param_grid": {"ma_short": [5,10], "ma_long": [20,50]},
    "seeds": [1,2,3],
    "total_jobs": int,
    "flags": {"VEK_STRAT_SWEEP": 1}
  }
- results/<run_id>/<strategy>/<param_hash>_equity.csv
- summary_<run_id>.json
  {
    "robust_cagr_median": float,
    "robust_cagr_p05": float,
    "robust_cagr_p95": float,
    "param_sensitivity_score": float,
    "failure_rate": float
  }
TODO: Decide param_hash = stable sorted key=value join + sha256.

## Regime Detection (I2)
Regime Label Schema:
  {
    "ts": iso8601,
    "vol_band": "low|mid|high",
    "trend_bucket": "down|flat|up",
    "regime": "HighVol-Up"
  }
TODO: Determine rolling window lengths (vol 14d, trend 20d slope?).

## Factor Attribution (I3)
Attribution Result Schema:
  {
    "window": "expanding|rolling",
    "betas": {"market": float, "momentum": float, "size": float},
    "alpha_residual_cagr": float,
    "r_squared": float,
    "factor_contrib_table": [ {"factor": str, "contrib_pct": float} ]
  }
TODO: Standardize period return frequency (daily synthetic from trades realignment).

## Portfolio Optimizer (I4)
Portfolio Run Spec:
  {
    "strategies": [ {"id": str, "equity_path": path, "policy": "equal|vol_parity|kelly|cap_dd" } ],
    "rebalance_cadence": "daily|weekly|monthly",
    "constraints": {"max_weight": 0.4, "min_strategies": 3}
  }
Output Metrics:
  {
    "portfolio_cagr": float,
    "portfolio_max_dd": float,
    "diversification_benefit": float,
    "turnover": float,
    "marginal_contributions": {"id": float}
  }
TODO: Kelly clamp range & volatility smoothing parameter.

## Failure Pattern Miner (I5)
Cluster Output Schema:
  {
    "cluster_id": int,
    "size": int,
    "avg_loss": float,
    "features_centroid": {"hold_minutes": float, "pre_runup_pct": float, "entry_vol": float},
    "narrative": str
  }
TODO: Feature engineering spec & silhouette score threshold.

---
All placeholders subject to refinement during implementation. Keep deterministic hashing & reproducibility priority.
