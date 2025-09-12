"""
# ============================================================
# Context Banner — test_simulation | Category: test
# Purpose: Testet Determinismus der Walk-Forward Simulation (gleicher Seed => gleiche Ergebnisse)

# Contracts
#   Inputs: synthetische Preisreihe, momentum_rule(2), seed
#   Outputs: Assertions auf final_cash & Hash-Gleichheit
#   Side-Effects: none
#   Determinism: deterministic (über Seed gesichert)

# Invariants
#   - Hash unverändert bei identischen Parametern

# Dependencies
#   Internal: sim.simple_walk
#   External: stdlib (datetime)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from datetime import datetime, timedelta
from app.sim.simple_walk import run_sim, momentum_rule


def test_sim_deterministic():
    prices = [(datetime(2024,1,1)+timedelta(days=i), 100 + i) for i in range(5)]
    r1 = run_sim(prices, momentum_rule(2), seed=42)
    r2 = run_sim(prices, momentum_rule(2), seed=42)
    assert r1.final_cash == r2.final_cash
    assert r1.meta['hash'] == r2.meta['hash']
