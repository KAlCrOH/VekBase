from datetime import datetime, timedelta
from app.sim.simple_walk import run_sim, momentum_rule


def test_sim_deterministic():
    prices = [(datetime(2024,1,1)+timedelta(days=i), 100 + i) for i in range(5)]
    r1 = run_sim(prices, momentum_rule(2), seed=42)
    r2 = run_sim(prices, momentum_rule(2), seed=42)
    assert r1.final_cash == r2.final_cash
    assert r1.meta['hash'] == r2.meta['hash']
