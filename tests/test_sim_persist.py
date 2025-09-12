from datetime import datetime, timedelta
from pathlib import Path
from app.sim.simple_walk import run_and_persist, momentum_rule


def test_run_and_persist(tmp_path: Path):
    prices = [(datetime(2024,1,1)+timedelta(days=i), 100 + i) for i in range(3)]
    res = run_and_persist(prices, momentum_rule(2), seed=7, results_dir=tmp_path)
    # one folder created
    folders = list(tmp_path.iterdir())
    assert len(folders) == 1
    meta = (folders[0] / 'meta.json').read_text(encoding='utf-8')
    assert 'hash' in meta and 'final_cash' in meta