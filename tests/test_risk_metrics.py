"""
# ============================================================
# Context Banner — test_risk_metrics | Category: test
# Purpose: Validate optional risk metrics (VaR & adverse stats) behind VEK_RISK_METRICS flag.
#
# Contracts
#   - Without flag: risk keys absent
#   - With flag: var_95, var_99, max_adverse_trade_return, max_adverse_trade_pnl present
#
# Dependencies
#   Internal: app.analytics.metrics, core.trade_model
#   External: stdlib
# ============================================================
"""
import os
from datetime import datetime
from app.analytics.metrics import aggregate_metrics
from app.core.trade_model import validate_trade_dict


def _sample_trades():
    # Construct deterministic trades with varied returns
    # Buy 10 @100, Sell 5 @110 (gain), Sell 5 @90 (loss)
    t1 = validate_trade_dict({'trade_id':'b1','ts':datetime(2024,1,1,10),'ticker':'XYZ','action':'BUY','shares':10,'price':100,'fees':0})
    t2 = validate_trade_dict({'trade_id':'s1','ts':datetime(2024,1,2,10),'ticker':'XYZ','action':'SELL','shares':5,'price':110,'fees':0})
    t3 = validate_trade_dict({'trade_id':'s2','ts':datetime(2024,1,3,10),'ticker':'XYZ','action':'SELL','shares':5,'price':90,'fees':0})
    return [t1, t2, t3]


def test_risk_metrics_flag_off(monkeypatch):
    monkeypatch.delenv('VEK_RISK_METRICS', raising=False)
    metrics = aggregate_metrics(_sample_trades())
    assert 'var_95' not in metrics
    assert 'var_99' not in metrics


def test_risk_metrics_flag_on(monkeypatch):
    monkeypatch.setenv('VEK_RISK_METRICS','1')
    metrics = aggregate_metrics(_sample_trades())
    assert 'var_95' in metrics and 'var_99' in metrics
    assert metrics['returns_sample_size'] == 2  # two SELL trades -> two returns
    # Worst trade return should be negative
    assert metrics['max_adverse_trade_return'] <= 0
    # VaR values non-negative
    assert metrics['var_95'] >= 0 and metrics['var_99'] >= 0