from math import isclose
from app.research.factor_attribution import returns_from_equity_curve, attribute_factors


def _make_equity_from_returns(rets):
    eq = 100.0
    curve = [(0, eq)]
    for i, r in enumerate(rets, start=1):
        eq = eq * (1 + r)
        curve.append((i, eq))
    return curve


def test_returns_from_equity_curve_basic():
    rets = [0.01, -0.02, 0.03]
    curve = _make_equity_from_returns(rets)
    out = returns_from_equity_curve(curve)
    assert all(isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) for a,b in zip(rets, out))


def test_single_factor_recovery_noise_free():
    # returns = 0.002 + 1.5 * factor
    factor = [0.01 * ((i % 5) - 2) for i in range(60)]  # centered oscillation
    returns = [0.002 + 1.5 * f for f in factor]
    res = attribute_factors(returns, {"F1": factor})
    assert isclose(res["betas"]["F1"], 1.5, rel_tol=1e-5, abs_tol=1e-5)
    assert isclose(res["alpha_mean"], 0.002, rel_tol=1e-6, abs_tol=1e-6)
    assert res["r_squared"] > 0.999999


def test_zero_factor_returns():
    returns = [0.0]*20
    factor = [0.1 * (i%3) for i in range(20)]
    res = attribute_factors(returns, {"F1": factor})
    # All zero returns => betas and alpha can be zero / model explains nothing special
    assert abs(res["alpha_mean"]) < 1e-12
    # r_squared undefined due to zero variance -> 0 per implementation
    assert res["r_squared"] == 0.0


def test_collinearity_handling():
    # Two identical factors; OLS with ridge should still produce stable output (betas may split influence)
    base = [0.01 * ((i%4)-1.5) for i in range(50)]
    returns = [0.001 + 2.0 * b for b in base]
    res = attribute_factors(returns, {"F1": base, "F2": list(base)})
    # Combined linear effect should approximate 2.0 when summing betas * mean(factor) scaled
    total_effect = res["betas"]["F1"] + res["betas"]["F2"]
    assert isclose(total_effect, 2.0, rel_tol=1e-3)


def test_insufficient_data():
    # Empty returns list
    res = attribute_factors([], {"F1": [0.1,0.2]})
    assert res["betas"] == {}
    assert res["r_squared"] == 0.0
