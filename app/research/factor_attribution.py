# ============================================================
# Context Banner — factor_attribution | Category: research
# Purpose: Attribute per-period returns to linear factors (betas) + residual (alpha proxy).
#
# Contracts
#   returns_from_equity_curve(equity_curve: list[(ts, equity)]) -> list[float]
#     Produces simple returns r_t = (E_t - E_{t-1}) / max(|E_{t-1}|, epsilon) with epsilon guard.
#   attribute_factors(returns: list[float], factors: dict[str, list[float]]) -> dict
#     Performs OLS: returns = alpha + sum(beta_i * factor_i) + residual.
#     Returns dict with betas, alpha_mean, alpha_cagr_proxy (annualized mean if >0), r_squared, residual_std, factor_contributions.
#
# Determinism: Pure numeric linear algebra (no randomness). Collinearity handled via pseudo-inverse with rank check.
# Dependencies: standard library only.
# ============================================================
from __future__ import annotations
from typing import List, Dict, Any
from math import sqrt, pow
from statistics import mean

EPS = 1e-9


def returns_from_equity_curve(curve: List[tuple]) -> List[float]:
    if len(curve) < 2:
        return []
    out: List[float] = []
    for i in range(1, len(curve)):
        prev = curve[i-1][1]
        cur = curve[i][1]
        denom = prev if abs(prev) > EPS else (EPS if prev >=0 else -EPS)
        out.append((cur - prev)/denom)
    return out


def _transpose(m: List[List[float]]) -> List[List[float]]:
    return [list(row) for row in zip(*m)] if m else []


def _matmul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    # a: n x k, b: k x m
    return [[sum(a[i][t]*b[t][j] for t in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


def _pinv(mat: List[List[float]]) -> List[List[float]]:
    # Basic pseudo-inverse via normal equations with fallback diagonal regularization.
    # mat: n x k (n observations, k variables)
    if not mat:
        return []
    t = _transpose(mat)  # k x n
    gram = _matmul(t, mat)  # k x k
    k = len(gram)
    # Add small ridge if near-singular
    det_approx = 0.0
    for i in range(k):
        det_approx += abs(gram[i][i])
    ridge = 1e-9 * (det_approx / k if k else 1.0)
    for i in range(k):
        gram[i][i] += ridge
    # Invert gram (use Gauss-Jordan since k expected small)
    inv = [[0.0]*k for _ in range(k)]
    for i in range(k):
        inv[i][i] = 1.0
    # Augmented matrix approach
    for col in range(k):
        pivot = gram[col][col]
        if abs(pivot) < 1e-12:
            gram[col][col] = 1e-12
            pivot = gram[col][col]
        inv_scale = 1.0/pivot
        for j in range(k):
            gram[col][j] *= inv_scale
            inv[col][j] *= inv_scale
        for r in range(k):
            if r == col: continue
            factor = gram[r][col]
            if factor == 0: continue
            for c in range(k):
                gram[r][c] -= factor * gram[col][c]
                inv[r][c] -= factor * inv[col][c]
    # pseudo inverse = (X^T X)^{-1} X^T
    return _matmul(inv, t)


def attribute_factors(returns: List[float], factors: Dict[str, List[float]]) -> Dict[str, Any]:
    # Align lengths
    if not returns:
        return {"betas": {}, "alpha_mean": 0.0, "alpha_cagr_proxy": 0.0, "r_squared": 0.0, "residual_std": 0.0, "factor_contributions": []}
    n = len(returns)
    factor_names = [k for k,v in factors.items() if len(v) == n]
    X: List[List[float]] = []
    for i in range(n):
        row: List[float] = [1.0]  # intercept
        for name in factor_names:
            row.append(factors[name][i])
        X.append(row)
    # Compute pseudo-inverse
    pinv = _pinv(X)  # (k x n)
    # beta vector = pinv * y
    y = [[r] for r in returns]
    beta_matrix = _matmul(pinv, y)  # k x 1
    betas_full = [b[0] for b in beta_matrix]
    intercept = betas_full[0] if betas_full else 0.0
    betas = {name: betas_full[i+1] for i, name in enumerate(factor_names)}
    # Fitted values
    fitted: List[float] = []
    for i in range(n):
        pred = intercept
        for j,name in enumerate(factor_names):
            pred += betas[name] * factors[name][i]
        fitted.append(pred)
    residuals = [returns[i] - fitted[i] for i in range(n)]
    ss_res = sum(r*r for r in residuals)
    mean_y = sum(returns)/n
    ss_tot = sum((r-mean_y)**2 for r in returns) if n>1 else 0.0
    r_squared = 1 - ss_res/ss_tot if ss_tot > 0 else 0.0
    residual_std = sqrt(ss_res/n) if n>0 else 0.0
    # Alpha proxies
    alpha_mean = intercept
    # Convert mean additive per-period return to CAGR proxy assuming periods ~ evenly spaced daily-like
    periods_per_year = 252  # assumption; adjust later if period type distinguished
    alpha_cagr_proxy = (pow(1+alpha_mean, periods_per_year) - 1) if alpha_mean > -1 else 0.0
    # Factor contribution heuristic: |beta * mean_factor| normalized
    contributions_raw = []
    for name in factor_names:
        mf = mean(factors[name]) if n>0 else 0.0
        contributions_raw.append((name, abs(betas[name] * mf)))
    total_c = sum(v for _,v in contributions_raw) or 1.0
    factor_contributions = [{"factor": name, "contribution_pct": (val/total_c)} for name,val in contributions_raw]
    return {
        "betas": betas,
        "alpha_mean": alpha_mean,
        "alpha_cagr_proxy": alpha_cagr_proxy,
        "r_squared": r_squared,
        "residual_std": residual_std,
        "factor_contributions": factor_contributions,
    }
