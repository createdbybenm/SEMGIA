import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from semgia import config
from semgia.evaluation import (
    FLOOR,
    ML_KINDS,
    SMOOTHED,
    confusion_markdown,
    confusions,
    final_predictions,
    lopo_predictions,
    markdown_table,
    score_table,
    scores,
    smooth,
    split_train_test,
)
from semgia.processing import sample_calibration, window_features
from semgia.storage import load_sample

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from make_mock_samples import make_sample  # noqa: E402
from train import load_all  # noqa: E402


@pytest.fixture(scope="module")
def samples(tmp_path_factory):
    """3 placements x 2 samples (one fresh, one fatigued), loaded like train.py does."""
    root = tmp_path_factory.mktemp("data")
    rng = np.random.default_rng(1)
    for e in (1, 2, 3):
        make_sample(root, e, rng, "medium", "fresh")
        make_sample(root, e, rng, "strong", "fatigued")
    return load_all(root)


def test_split_never_mixes_placements(samples, monkeypatch):
    monkeypatch.setattr(config, "TEST_PLACEMENTS", ["E03"])
    train, test = split_train_test(samples)
    assert {s["placement"] for s in test} == {"E03"}
    assert "E03" not in {s["placement"] for s in train}
    assert len(train) + len(test) == len(samples)


def test_lopo_uses_train_only(samples, monkeypatch):
    monkeypatch.setattr(config, "TEST_PLACEMENTS", ["E03"])
    train, _ = split_train_test(samples)
    preds = lopo_predictions(train)
    assert {p["placement"] for p in preds} == {"E01", "E02"}
    table = score_table(preds)
    assert set(table.model) == {FLOOR, *ML_KINDS}
    assert set(table.windows) == {"clean", "all", SMOOTHED}
    assert (table.balanced_accuracy > 0.9).all()


def test_lopo_needs_two_placements(samples):
    with pytest.raises(ValueError):
        lopo_predictions([s for s in samples if s["placement"] == "E01"])


def test_final_refuses_without_test_set(samples, monkeypatch):
    monkeypatch.setattr(config, "TEST_PLACEMENTS", [])
    with pytest.raises(ValueError):
        final_predictions(samples, [])
    monkeypatch.setattr(config, "TEST_PLACEMENTS", ["E09"])   # defined, but not recorded
    with pytest.raises(ValueError):
        final_predictions(*split_train_test(samples))


def test_final_scores_test_placements(samples, monkeypatch):
    monkeypatch.setattr(config, "TEST_PLACEMENTS", ["E03"])
    preds = final_predictions(*split_train_test(samples))
    assert {p["placement"] for p in preds} == {"E03"}
    by_cond = score_table(preds, by=["condition"])
    assert set(by_cond.condition) == {"fresh", "fatigued"}


def test_scores_and_chance_floor():
    y = np.array([0, 0, 0, 1])
    s = scores(y, np.zeros(4, dtype=int))          # always "rest"
    assert s["accuracy"] == s["chance"] == 0.75
    assert s["balanced_accuracy"] == 0.5


def test_confusion_rows_are_true_labels(samples, monkeypatch):
    monkeypatch.setattr(config, "TEST_PLACEMENTS", ["E03"])
    preds = final_predictions(*split_train_test(samples))
    cm = confusions(preds)[FLOOR]
    floor_all = [p for p in preds if p["model"] == FLOOR and p["windows"] == "all"]
    n_true_contract = sum(int((p["y"] == config.CONTRACT).sum()) for p in floor_all)
    assert cm.shape == (2, 2) and cm[1].sum() == n_true_contract
    assert "pred contract" in confusion_markdown(confusions(preds))


def test_smooth_removes_single_flicker():
    pred = np.array([0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1])
    out = smooth(pred)
    assert out[3] == 0                       # one stray "contract" is voted away
    assert out[-1] == 1 and len(out) == len(pred)


def test_lda_is_in_the_comparison():
    assert "lda" in ML_KINDS


def test_markdown_table_rounds_floats():
    md = markdown_table(pd.DataFrame({"model": ["a"], "acc": [0.123456]}))
    assert md.splitlines() == ["| model | acc |", "|---|---|", "| a | 0.123 |"]


def test_sample_calibration_first_rest_becomes_1(tmp_path):
    df, _ = load_sample(make_sample(tmp_path, 1, np.random.default_rng(0)))
    labels = df["label"].to_numpy()
    ends, feats = window_features(df["value"].to_numpy())
    rms = sample_calibration(labels, ends, feats).normalize(feats)[:, 0]
    first_rest = ends < config.SAMPLE_STEPS[0][1] * config.FS
    assert abs(np.median(rms[first_rest]) - 1) < 0.1
    with pytest.raises(ValueError):
        sample_calibration(1 - labels, ends, feats)   # must start with rest
