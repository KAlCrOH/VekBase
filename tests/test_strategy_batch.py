# Tests for research.strategy_batch
from app.research.strategy_batch import (
    run_strategy_batch,
    MovingAverageCrossover,
    RandomFlip,
)

# Helper: simple quantile replicating internal logic

def _q(vals, q: float):
    if not vals:
        return 0.0
    if q <= 0:
        return vals[0]
    if q >= 1:
        return vals[-1]
    pos = (len(vals) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(vals) - 1)
    frac = pos - lo
    return vals[lo] * (1 - frac) + vals[hi] * frac


def test_strategy_batch_basic_deterministic():
    price_series = [100 + (i * 0.1) for i in range(120)]  # gentle uptrend
    strategies = [MovingAverageCrossover(), RandomFlip()]
    param_grid = {"ma_short": [3, 4], "ma_long": [10]}  # 2 combinations
    seeds = [1, 2]

    results1, summary1 = run_strategy_batch(strategies, price_series, param_grid, seeds)
    results2, summary2 = run_strategy_batch(strategies, price_series, param_grid, seeds)

    # Determinism: identical outputs
    assert results1 == results2
    assert summary1 == summary2

    # Run count expectations: 2 strategies * 2 param combos * 2 seeds = 8
    assert summary1["runs"] == 8
    assert summary1["param_combinations"] == 2
    assert set(summary1["strategies"]) == {"ma_crossover", "random_flip"}

    # Quantile checks: recompute from results' CAGR values
    cagr_vals = sorted(r["metrics"]["cagr"] for r in results1)
    assert summary1["robust_cagr_median"] == _q(cagr_vals, 0.5)
    assert summary1["robust_cagr_p05"] == _q(cagr_vals, 0.05)
    assert summary1["robust_cagr_p95"] == _q(cagr_vals, 0.95)
    # Monotonic quantile ordering
    assert summary1["robust_cagr_p05"] <= summary1["robust_cagr_median"] <= summary1["robust_cagr_p95"]

    # Failure rate recomputation
    failure_dd_threshold = 0.3
    dd_values = [r["metrics"]["max_drawdown_realized"] for r in results1]
    recomputed_failure_rate = sum(1 for d in dd_values if d > failure_dd_threshold) / len(dd_values)
    assert summary1["failure_rate"] == recomputed_failure_rate

    # Param sensitivity recomputation (replicate internal logic)
    by_param = {}
    for r in results1:
        by_param.setdefault(r["param_hash"], []).append(r["metrics"]["cagr"])
    cagr_values = [r["metrics"]["cagr"] for r in results1]
    if len(by_param) > 1:
        global_mean = sum(cagr_values) / len(cagr_values)
        group_means = [sum(v) / len(v) for v in by_param.values()]
        group_var = sum((m - global_mean) ** 2 for m in group_means) / len(group_means)
        recomputed_param_sens = group_var ** 0.5
    else:
        recomputed_param_sens = 0.0
    assert summary1["param_sensitivity_score"] == recomputed_param_sens


def test_strategy_batch_single_param_combo_sensitivity_zero():
    price_series = [100 + (i * 0.2) for i in range(80)]
    strategies = [MovingAverageCrossover()]
    param_grid = {"ma_short": [3], "ma_long": [12]}  # single combination
    seeds = [42, 99]

    _results, summary = run_strategy_batch(strategies, price_series, param_grid, seeds)
    assert summary["param_combinations"] == 1
    assert summary["param_sensitivity_score"] == 0.0
    assert summary["runs"] == 2  # 1 strategy * 1 combo * 2 seeds


def test_strategy_batch_empty_inputs():
    # Edge: no strategies
    price_series = [101, 102, 103]
    strategies = []
    param_grid = {"x": [1, 2]}
    seeds = [1]

    results, summary = run_strategy_batch(strategies, price_series, param_grid, seeds)
    assert results == []
    assert summary["runs"] == 0
    # Basic keys present
    for k in [
        "robust_cagr_median",
        "robust_cagr_p05",
        "robust_cagr_p95",
        "failure_rate",
        "param_sensitivity_score",
    ]:
        assert k in summary
