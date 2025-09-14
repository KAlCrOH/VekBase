from math import isclose
from datetime import datetime, UTC, timedelta
from app.research.portfolio_optimizer import (
    build_returns_matrix,
    allocate_weights,
    assemble_portfolio,
    portfolio_metrics,
)

# Helper: construct equity curves with controllable volatility

def _equity_curve_from_returns(label, base_ts, returns):
    eq = 100.0
    curve = []
    for i, r in enumerate(returns):
        ts = base_ts + timedelta(days=i)
        curve.append((ts, eq))
        eq *= (1 + r)
    # append final point
    ts = base_ts + timedelta(days=len(returns))
    curve.append((ts, eq))
    return label, curve


def test_build_returns_matrix_alignment():
    base = datetime(2025,1,1,tzinfo=UTC)
    r1 = [0.01]*10
    r2 = [0.02]*10
    name1, c1 = _equity_curve_from_returns("S1", base, r1)
    name2, c2 = _equity_curve_from_returns("S2", base, r2)
    ts, mat = build_returns_matrix({name1: c1, name2: c2})
    assert len(ts) == 10  # returns length
    assert len(mat["S1"]) == 10 and len(mat["S2"]) == 10
    assert all(isclose(x, 0.01) for x in mat["S1"]) and all(isclose(x, 0.02) for x in mat["S2"]) 


def test_equal_weight_portfolio_metrics():
    base = datetime(2025,1,1,tzinfo=UTC)
    r1 = [0.01]*30
    r2 = [0.02]*30
    name1, c1 = _equity_curve_from_returns("A", base, r1)
    name2, c2 = _equity_curve_from_returns("B", base, r2)
    ts, ret_mat = build_returns_matrix({name1: c1, name2: c2})
    weights = allocate_weights(ret_mat, policy="equal_weight")
    curve = assemble_portfolio(ts, ret_mat, weights)
    metrics = portfolio_metrics(curve, ret_mat, weights)
    # CAGR should be between individual strategies' implied rate
    assert 0 < metrics["portfolio_cagr"] < 0.02*252  # rough upper bound (not annualized exactly but within bounds)
    assert metrics["diversification_benefit"] >= 0.0


def test_vol_parity_weights_inverse_vol():
    base = datetime(2025,1,1,tzinfo=UTC)
    # Strategy A high vol, B low vol
    rA = [0.05 if i%2==0 else -0.05 for i in range(40)]
    rB = [0.01 if i%2==0 else -0.01 for i in range(40)]
    A, cA = _equity_curve_from_returns("A", base, rA)
    B, cB = _equity_curve_from_returns("B", base, rB)
    ts, ret_mat = build_returns_matrix({A: cA, B: cB})
    weights = allocate_weights(ret_mat, policy="vol_parity")
    # Expect weight on high vol < weight on low vol
    assert weights["A"] < weights["B"]
    assert isclose(sum(weights.values()), 1.0, rel_tol=1e-6)


def test_max_dd_capped_scaling():
    base = datetime(2025,1,1,tzinfo=UTC)
    r1 = [0.05]*20  # strong up
    r2 = [-0.02]*20  # down
    S1, c1 = _equity_curve_from_returns("S1", base, r1)
    S2, c2 = _equity_curve_from_returns("S2", base, r2)
    ts, ret_mat = build_returns_matrix({S1: c1, S2: c2})
    w_uncapped = allocate_weights(ret_mat, policy="vol_parity")
    w_capped = allocate_weights(ret_mat, policy="max_dd_capped", max_dd_cap=0.05)
    # Scaled weights sum <= uncapped sum
    assert sum(w_capped.values()) <= sum(w_uncapped.values())


def test_identical_strategies_zero_diversification():
    base = datetime(2025,1,1,tzinfo=UTC)
    returns = [0.01 if i%2==0 else -0.01 for i in range(50)]
    A, cA = _equity_curve_from_returns("A", base, returns)
    B, cB = _equity_curve_from_returns("B", base, returns)
    ts, ret_mat = build_returns_matrix({A: cA, B: cB})
    weights = allocate_weights(ret_mat, policy="equal_weight")
    curve = assemble_portfolio(ts, ret_mat, weights)
    metrics = portfolio_metrics(curve, ret_mat, weights)
    # Correlated identical series => diversification benefit ~ 0
    assert metrics["diversification_benefit"] < 0.05
