from app.ui import strategy_batch_ui as sbu


def test_strategy_batch_ui_happy():
    strategies = '["ma_crossover","random_flip"]'
    param_grid = '{"ma_short":[5],"ma_long":[15],"flip_prob":[0.05]}'
    seeds = '1'
    res = sbu.run_strategy_batch_ui(strategies, param_grid, seeds)
    assert 'error' not in res
    assert res['summary']['runs'] == 2  # two strategies * 1 combo * 1 seed
    assert isinstance(res['results'], list) and len(res['results']) == 2


def test_strategy_batch_ui_invalid_json():
    res = sbu.run_strategy_batch_ui('not-json', '{}', '1')
    assert 'error' in res and 'parse error' in res['error']


def test_strategy_batch_ui_empty_strategies():
    res = sbu.run_strategy_batch_ui('[]', '{}', '1')
    assert 'error' in res and 'no strategies' in res['error']


def test_strategy_batch_ui_missing_seeds():
    res = sbu.run_strategy_batch_ui('["ma_crossover"]', '{}', '')
    assert 'error' in res and 'no seeds' in res['error']


def test_strategy_batch_ui_unknown_strategy():
    res = sbu.run_strategy_batch_ui('["does_not_exist"]', '{}', '1')
    assert 'error' in res and 'unknown strategy' in res['error']
