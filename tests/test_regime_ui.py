from app.ui import regime_ui as rui


def test_regime_ui_happy_labels_and_segments():
    prices = [100 + i*0.5 + ((i%5)-2)*0.1 for i in range(60)]
    labels = rui.prepare_regime_labels(prices)
    assert labels and len(labels) == len(prices)
    reg = rui.summarize_regimes([], prices)
    assert 'summary' in reg
    segs = rui.compute_overlay_segments(labels)
    assert segs and segs[0]['start_idx'] <= segs[0]['end_idx']


def test_regime_ui_short_series():
    prices = [100, 101, 102]
    labels = rui.prepare_regime_labels(prices)
    assert labels == []
    reg = rui.summarize_regimes([], prices)
    assert reg['labels'] == []


def test_regime_ui_segments_integrity():
    prices = [100 + i for i in range(30)]
    labels = rui.prepare_regime_labels(prices)
    segs = rui.compute_overlay_segments(labels)
    last_end = -1
    for s in segs:
        assert s['start_idx'] <= s['end_idx']
        assert s['start_idx'] > last_end
        last_end = s['end_idx']
