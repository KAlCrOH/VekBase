"""
# ============================================================
# Context Banner — research_preview | Category: ui
# Purpose: Lightweight, streamlit-freie Helper für Research Preview Panels (Factor Attribution & Portfolio) zur Nutzung im Console Analytics Tab.
#
# Contracts
#   attribution_preview(equity_curve:list[(ts,eq)]) -> dict(status, betas, alpha_cagr_proxy, r_squared, top_factor, artifact_path|None)
#   portfolio_preview(equity_curve:list[(ts,eq)]) -> dict(status, policy, weights, metrics:{...}, artifact_path|None)
#   panels_enabled() -> bool  (prüft Flags VEK_ATTRIBUTION / VEK_PORTFOLIO)
#
# Invariants
#   - Keine externen Dependencies (nur stdlib + vorhandene research module)
#   - Artefakte unter ./.artifacts/research/{attribution|portfolio}/<run_id>_summary.json
#   - Keine Exceptions nach außen; Fehler -> status='error' + message
#   - Deterministisch (synthetische Faktoren & alternative Kurve rein deterministisch)
#
# Tests
#   tests/test_research_preview.py
#
# Do-Not-Change
#   Banner policy-relevant (Änderungen nur via spezifische Task)
# ============================================================
"""
from __future__ import annotations
from typing import List, Tuple, Dict, Any
import os, json, time, uuid
from pathlib import Path

from app.research import factor_attribution as _attr
from app.research import portfolio_optimizer as _port

__all__ = [
    "attribution_preview",
    "portfolio_preview",
    "panels_enabled",
]


def _run_id() -> str:
    return f"{int(time.time())}-{uuid.uuid4().hex[:6]}"


def _artifact_path(kind: str, run_id: str) -> Path:
    p = Path('.artifacts') / 'research' / kind
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{run_id}_summary.json"


def panels_enabled() -> bool:
    return bool(int(os.environ.get("VEK_ATTRIBUTION", "1"))) or bool(int(os.environ.get("VEK_PORTFOLIO", "1")))


def attribution_preview(equity_curve: List[Tuple]) -> Dict[str, Any]:
    if not equity_curve or len(equity_curve) < 4:
        return {"status": "empty", "artifact_path": None}
    try:
        returns = _attr.returns_from_equity_curve(equity_curve)
        n = len(returns)
        if n < 3:
            return {"status":"empty","artifact_path":None}
        # Synthetische Faktoren (deterministisch)
        trend = [i/(n-1) for i in range(n)]
        mom = []
        for i,r in enumerate(returns):
            prev = returns[i-1] if i>0 else returns[0]
            mom.append(abs(r - prev))
        # Normierung
        def _norm(xs: List[float]) -> List[float]:
            mx = max(xs) if xs else 1.0
            return [x/mx if mx else 0.0 for x in xs]
        factors = {"trend": _norm(trend), "momentum": _norm(mom)}
        res = _attr.attribute_factors(returns, factors)
        # Top factor by contribution
        contrib = res.get("factor_contributions") or []
        top_factor = None
        if contrib:
            top = sorted(contrib, key=lambda x: x.get("contribution_pct",0), reverse=True)[0]
            top_factor = top.get("factor")
        payload = {
            "status": "ok",
            "betas": res.get("betas"),
            "alpha_cagr_proxy": res.get("alpha_cagr_proxy"),
            "r_squared": res.get("r_squared"),
            "top_factor": top_factor,
        }
        run_id = _run_id()
        try:
            ap = _artifact_path('attribution', run_id)
            ap.write_text(json.dumps({**payload, "run_id": run_id}, ensure_ascii=False, indent=2), encoding='utf-8')
            payload["artifact_path"] = str(ap)
        except Exception:
            payload["artifact_path"] = None
        return payload
    except Exception as e:
        return {"status":"error","message":str(e),"artifact_path":None}


def _alt_curve(base: List[Tuple]) -> List[Tuple]:
    # Deterministischer kleiner Oszillationsfaktor
    out: List[Tuple] = []
    for i,(ts,v) in enumerate(base):
        adj = v * (1 + 0.002 * ((i % 5) - 2))
        out.append((ts, adj))
    return out


def portfolio_preview(equity_curve: List[Tuple]) -> Dict[str, Any]:
    if not equity_curve or len(equity_curve) < 4:
        return {"status": "empty", "artifact_path": None}
    try:
        alt = _alt_curve(equity_curve)
        ec_map = {"base": equity_curve, "alt": alt}
        ts, returns_by = _port.build_returns_matrix(ec_map)
        if not ts:
            return {"status":"empty","artifact_path":None}
        weights = _port.allocate_weights(returns_by, policy="vol_parity")
        curve = _port.assemble_portfolio(ts, returns_by, weights)
        metrics = _port.portfolio_metrics(curve, returns_by, weights)
        payload = {
            "status": "ok",
            "policy": "vol_parity",
            "weights": weights,
            "metrics": metrics,
        }
        run_id = _run_id()
        try:
            ap = _artifact_path('portfolio', run_id)
            ap.write_text(json.dumps({**payload, "run_id": run_id}, ensure_ascii=False, indent=2), encoding='utf-8')
            payload["artifact_path"] = str(ap)
        except Exception:
            payload["artifact_path"] = None
        return payload
    except Exception as e:
        return {"status":"error","message":str(e),"artifact_path":None}
