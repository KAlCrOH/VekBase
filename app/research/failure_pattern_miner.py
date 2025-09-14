# ============================================================
# Context Banner — failure_pattern_miner | Category: research
# Purpose: Extract and cluster realized losing trade patterns to surface repetitive failure modes.
#
# Contracts
#   extract_loss_features(trades) -> List[dict]
#     Each feature row: {trade_id, pct_loss, abs_loss, holding_duration_sec, entry_hour_norm, position_size, vol_proxy}
#   cluster_losses(feature_rows, k_max=5) -> List[dict]
#     Deterministic centroid initialization (farthest-first), returns cluster assignments & centroids in normalized space.
#   summarize_loss_clusters(trades, clusters) -> Dict[str, Any]
#     Produces loss_clusters (summary) + avoidable_loss_estimate (sum of top 2 cluster abs losses).
#
# Determinism: No randomness; ordering-based selection for centroids.
# ============================================================
from __future__ import annotations
from typing import List, Dict, Any, Tuple
from math import sqrt
from datetime import datetime
from ..analytics.metrics import compute_realized_pnl
from ..core.trade_model import Trade

EPS = 1e-12


def extract_loss_features(trades: List[Trade]) -> List[Dict[str, Any]]:
    pnl_entries, _ = compute_realized_pnl(trades)
    # Map trade_id->holding duration approx by looking up BUY->SELL time differences
    # Build simple inventory again to capture entry ts for sells
    buy_ts: Dict[str, List[Tuple[float, float, datetime]]] = {}
    for t in sorted(trades, key=lambda x: x.ts):
        if t.action == "BUY":
            buy_ts.setdefault(t.ticker, []).append((t.shares, t.price, t.ts))
        else:
            remaining = t.shares
            lots = buy_ts.get(t.ticker, [])
            i = 0
            while remaining > 1e-12 and i < len(lots):
                lot_sh, lot_price, lot_time = lots[i]
                take = min(lot_sh, remaining)
                lot_sh -= take
                remaining -= take
                if lot_sh <= 1e-12:
                    lots.pop(i)
                else:
                    lots[i] = (lot_sh, lot_price, lot_time)
                    i += 1
    features: List[Dict[str, Any]] = []
    # Build SELL trade lookup for durations (using cost_basis stored in pnl_entries)
    pnl_by_trade: Dict[str, Any] = {p.trade.trade_id: p for p in pnl_entries}
    # Precompute simple rolling volatility proxy: std of price deltas over entire trade set per ticker (coarse)
    prices_by_ticker: Dict[str, List[float]] = {}
    for t in sorted(trades, key=lambda x: x.ts):
        prices_by_ticker.setdefault(t.ticker, []).append(t.price)
    vol_proxy_ticker: Dict[str, float] = {}
    for tk, arr in prices_by_ticker.items():
        if len(arr) < 2:
            vol_proxy_ticker[tk] = 0.0
        else:
            deltas = [arr[i]-arr[i-1] for i in range(1, len(arr))]
            m = sum(deltas)/len(deltas)
            var = sum((d-m)**2 for d in deltas)/len(deltas)
            vol_proxy_ticker[tk] = var**0.5
    # Iterate entries where realized loss
    for p in pnl_entries:
        if p.realized_pnl >= 0:
            continue
        trade = p.trade
        cost_basis = p.cost_basis if p.cost_basis > 0 else 1.0
        pct_loss = p.realized_pnl / cost_basis  # negative
        abs_loss = -p.realized_pnl
        # Holding duration: Since compute_realized_pnl doesn't directly attach durations, approximate: 0 (placeholder for improvement)
        holding_duration_sec = 0.0
        entry_hour_norm = (trade.ts.hour + trade.ts.minute/60)/24.0
        position_size = trade.shares * trade.price
        vol_proxy = vol_proxy_ticker.get(trade.ticker, 0.0)
        features.append({
            "trade_id": trade.trade_id,
            "pct_loss": pct_loss,
            "abs_loss": abs_loss,
            "holding_duration_sec": holding_duration_sec,
            "entry_hour_norm": entry_hour_norm,
            "position_size": position_size,
            "vol_proxy": vol_proxy,
        })
    return features


def _zscore(rows: List[Dict[str, Any]], keys: List[str]) -> Tuple[List[List[float]], Dict[str, Tuple[float,float]]]:
    if not rows:
        return [], {}
    stats: Dict[str, Tuple[float,float]] = {}
    for k in keys:
        vals = [row[k] for row in rows]
        mean = sum(vals)/len(vals)
        var = sum((v-mean)**2 for v in vals)/len(vals) if len(vals) > 0 else 0.0
        std = var**0.5
        if std < EPS:
            std = 1.0
        stats[k] = (mean, std)
    mat: List[List[float]] = []
    for row in rows:
        mat.append([(row[k]-stats[k][0])/stats[k][1] for k in keys])
    return mat, stats


def _euclid(a: List[float], b: List[float]) -> float:
    return sqrt(sum((x-y)**2 for x,y in zip(a,b)))


def cluster_losses(feature_rows: List[Dict[str, Any]], k_max: int = 5) -> List[Dict[str, Any]]:
    if not feature_rows:
        return []
    numeric_keys = ["pct_loss", "holding_duration_sec", "entry_hour_norm", "position_size", "vol_proxy"]
    mat, stats = _zscore(feature_rows, numeric_keys)
    n = len(mat)
    k = min(k_max, n)
    # Centroid initialization: first = row with median pct_loss, subsequent farthest from existing centroids
    sorted_by_loss = sorted(range(n), key=lambda i: feature_rows[i]["pct_loss"])  # pct_loss negative; median more central
    first_idx = sorted_by_loss[len(sorted_by_loss)//2]
    centroids = [mat[first_idx]]
    chosen = {first_idx}
    while len(centroids) < k:
        # pick farthest point from nearest centroid
        best_i = None
        best_dist = -1.0
        for i in range(n):
            if i in chosen:
                continue
            dmin = min(_euclid(mat[i], c) for c in centroids)
            if dmin > best_dist:
                best_dist = dmin
                best_i = i
        if best_i is None:
            break
        chosen.add(best_i)
        centroids.append(mat[best_i])
    # Single refinement iterations (limit 5)
    assignments = [0]*n
    for iteration in range(5):
        changed = False
        # assign
        for i in range(n):
            dists = [_euclid(mat[i], c) for c in centroids]
            new_cluster = dists.index(min(dists))
            if new_cluster != assignments[i]:
                assignments[i] = new_cluster
                changed = True
        # recompute
        new_centroids: List[List[float]] = []
        for ci in range(len(centroids)):
            members = [mat[i] for i,a in enumerate(assignments) if a == ci]
            if not members:
                new_centroids.append(centroids[ci])
            else:
                dim = len(members[0])
                new_centroids.append([sum(m[j] for m in members)/len(members) for j in range(dim)])
        centroids = new_centroids
        if not changed:
            break
    # Build cluster summaries
    clusters: List[Dict[str, Any]] = []
    for ci in range(len(centroids)):
        members_idx = [i for i,a in enumerate(assignments) if a == ci]
        if not members_idx:
            continue
        members = [feature_rows[i] for i in members_idx]
        avg_pct_loss = sum(m["pct_loss"] for m in members)/len(members)
        avg_abs_loss = sum(m["abs_loss"] for m in members)/len(members)
        # Top features: largest absolute z-score average per feature
        feature_scores: List[Tuple[str, float]] = []
        for k in numeric_keys:
            # average absolute z for feature
            z_vals = [ (m[k]-stats[k][0]) / stats[k][1] for m in members ]
            feature_scores.append((k, sum(abs(z) for z in z_vals)/len(z_vals)))
        feature_scores.sort(key=lambda x: x[1], reverse=True)
        clusters.append({
            "cluster_id": ci,
            "size": len(members),
            "avg_pct_loss": avg_pct_loss,
            "avg_abs_loss": avg_abs_loss,
            "top_features": feature_scores[:3],
        })
    # Order clusters by avg_abs_loss desc for stability
    clusters.sort(key=lambda c: c["avg_abs_loss"], reverse=True)
    return clusters


def summarize_loss_clusters(trades: List[Trade], clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not clusters:
        return {"loss_clusters": [], "avoidable_loss_estimate": 0.0}
    # Avoidable loss heuristic: sum avg_abs_loss * size for top 2 clusters
    top = clusters[:2]
    avoidable = sum(c["avg_abs_loss"] * c["size"] for c in top)
    return {"loss_clusters": clusters, "avoidable_loss_estimate": avoidable}
