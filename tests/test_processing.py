import numpy as np

from semgia import config
from semgia.processing import Calibration, Filter, Windower, clean_mask, features, window_features
from semgia.recorder import SAMPLE_N, label_at


def test_windower_same_result_chunked_and_whole():
    x = np.random.default_rng(0).normal(size=2000)
    whole = Windower().push(x)
    w = Windower()
    chunked = [p for chunk in np.array_split(x, 37) for p in w.push(chunk)]
    assert len(whole) == len(chunked) == (2000 - config.WINDOW) // config.STEP + 1
    for (e1, w1), (e2, w2) in zip(whole, chunked):
        assert e1 == e2 and np.allclose(w1, w2)


def test_filter_chunked_equals_whole():
    x = 512 + np.random.default_rng(1).normal(size=3000)
    whole = Filter().process(x)
    f = Filter()
    chunked = np.concatenate([f.process(c) for c in np.array_split(x, 11)])
    assert np.allclose(whole, chunked)


def test_envelope_mode_keeps_sustained_level():
    x = np.r_[np.full(2000, 20.0), np.full(8000, 300.0)]
    assert np.allclose(Filter(raw=False).process(x), x)


def test_features_of_known_signal():
    w = np.array([1.0, -1.0, 1.0, -1.0])
    rms, mav, wl, zc = features(w)
    assert rms == 1 and mav == 1 and wl == 6 and zc == 3


def test_calibration_rest_becomes_1():
    cal = Calibration.from_rest(np.array([[2.0, 4.0], [2.0, 4.0]]))
    assert np.allclose(cal.normalize(np.array([2.0, 4.0])), 1)
    assert np.allclose(cal.normalize(np.array([10.0, 4.0])), [5, 1])


def test_labels_follow_protocol():
    labels = label_at(np.arange(SAMPLE_N))
    assert SAMPLE_N == 24 * config.FS
    assert (labels[:8000] == 0).all() and (labels[8000:16000] == 1).all() and (labels[16000:] == 0).all()


def test_clean_mask_keeps_middle_5s_of_each_phase():
    labels = label_at(np.arange(SAMPLE_N))
    ends, _ = window_features(np.zeros(SAMPLE_N))
    keep = clean_mask(ends, np.flatnonzero(np.diff(labels)) + 1, SAMPLE_N)
    starts = ends[keep] - config.WINDOW
    for a, b in [(0, 8000), (8000, 16000), (16000, 24000)]:
        inside = (starts >= a) & (ends[keep] <= b)
        assert starts[inside].min() >= a + 1500 and ends[keep][inside].max() <= b - 1500
        assert inside.sum() >= 45  # ~5 s of windows every 100 ms
    assert len(set(labels[ends[keep] - 1])) == 2
