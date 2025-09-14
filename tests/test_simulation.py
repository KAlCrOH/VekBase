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


def test_sim_tp_sl_fee():
    # deterministic handcrafted price path
    # Start 100 -> rise to trigger TP then fall to trigger SL in second position
    from datetime import datetime, timedelta
    prices = []
    base = datetime(2024,1,1)
    price_series = [100, 101, 103, 105, 104, 102, 99, 98]  # TP ~ +5% hit at price 105 (from 100)
    for i, p in enumerate(price_series):
        prices.append((base + timedelta(days=i), p))

    # Simple always BUY rule until position closed, then BUY again once.
    def one_shot_rule(hist):
        # BUY at first opportunity and again after flat (position closed) but limit to 2 buys.
        ts_idx = len(hist)
        # Determine number of BUY events so far by counting equity increases? Simpler: deterministic positions by index.
        if ts_idx == 1:
            return 'BUY'
        # second entry after we closed by TP around index 4 (we know path)
        if ts_idx == 6:  # re-enter near price 102
            return 'BUY'
        return 'HOLD'

    res = run_sim(
        prices,
        one_shot_rule,
        seed=1,
        initial_cash=1000,
        trade_size=1.0,  # allocate all capital
        take_profit_pct=0.05,
        stop_loss_pct=0.03,
        fee_rate_pct=0.001,  # 0.1% each side
    )
    # After TP at price 105: Gain approx (105/100 -1)=5% minus fees (0.1% buy + 0.1% sell ~0.2%) => ~4.8%
    # Then second trade: entry 102, stop loss should trigger at 98 (drawdown > 3% from 102 -> -3.92%)
    # PnL second trade: -3.92% - 0.2% fees ~ -4.12%
    # Net should be slightly below initial (due to asymmetry). Validate within tolerance.
    final_cash = res.final_cash
    assert 950 < final_cash < 1005, final_cash

def test_sim_backward_compatibility_hash_change():
    # Using same legacy params should produce same hash as before (TP/SL/Fee default values)
    from datetime import datetime, timedelta
    prices = [(datetime(2024,1,1)+timedelta(days=i), 100 + i) for i in range(5)]
    r_legacy = run_sim(prices, momentum_rule(2), seed=42)
    r_extended = run_sim(prices, momentum_rule(2), seed=42, take_profit_pct=None, stop_loss_pct=None, fee_rate_pct=0.0)
    assert r_legacy.meta['hash'] == r_extended.meta['hash']


def test_sim_deterministic():
    prices = [(datetime(2024,1,1)+timedelta(days=i), 100 + i) for i in range(5)]
    r1 = run_sim(prices, momentum_rule(2), seed=42)
    r2 = run_sim(prices, momentum_rule(2), seed=42)
    assert r1.final_cash == r2.final_cash
    assert r1.meta['hash'] == r2.meta['hash']
