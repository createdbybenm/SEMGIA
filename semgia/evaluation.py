"""Fair-split evaluation (course rule): choose on the train placements, open the test placements once.

A "sample dict" is what scripts/train.py:load_all returns:
    {"id", "placement", "condition", "effort", "X", "y" (clean windows), "X_all", "y_all" (every window)}

Every model predicts each sample separately (like live), and all predictions are pooled before scoring.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix

from semgia import config
from semgia.model import MLModel, ThresholdModel
from semgia.report import split_of

FLOOR = "threshold (floor)"     # ThresholdModel: one threshold on one feature = the floor to beat
ML_KINDS = ["logreg", "forest"]  # MLModel kinds to compare. A new kind in model.py -> add its name here.
WINDOW_SETS = {"clean": "", "all": "_all"}   # "clean" = middle of each phase, "all" = every window (live)


def split_train_test(samples: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split by config.TEST_PLACEMENTS. A placement is never on both sides."""
    train = [s for s in samples if split_of(s["placement"]) == "train"]
    test = [s for s in samples if split_of(s["placement"]) == "test"]
    return train, test


def build_models(train: list[dict]) -> dict:
    """The floor + every ML kind, fitted on the clean windows of `train`."""
    X = np.vstack([s["X"] for s in train])
    y = np.concatenate([s["y"] for s in train])
    return {FLOOR: ThresholdModel(), **{k: MLModel(k).fit(X, y) for k in ML_KINDS}}


def predict(models: dict, test: list[dict]) -> list[dict]:
    """One record per (model, sample, window set): true labels y and predictions."""
    out = []
    for name, model in models.items():
        for s in test:
            for windows, key in WINDOW_SETS.items():
                out.append({"model": name, "sample": s["id"], "placement": s["placement"],
                            "condition": s.get("condition", ""), "windows": windows,
                            "y": s["y" + key], "pred": model.predict_many(s["X" + key])})
    return out


def lopo_predictions(train: list[dict]) -> list[dict]:
    """Leave-one-placement-out inside the TRAIN samples.
    Each placement is predicted by models that never saw it (= electrodes re-applied)."""
    placements = sorted({s["placement"] for s in train})
    if len(placements) < 2:
        raise ValueError("need at least 2 train placements (E01, E02, ...) for leave-one-placement-out")
    out = []
    for held in placements:
        fit_on = [s for s in train if s["placement"] != held]
        out += predict(build_models(fit_on), [s for s in train if s["placement"] == held])
    return out


def final_predictions(train: list[dict], test: list[dict]) -> list[dict]:
    """Final run: fit on ALL train samples, predict the test samples. Only call this once, at the end."""
    if not config.TEST_PLACEMENTS:
        raise ValueError("config.TEST_PLACEMENTS is empty - define the test placements first")
    if not test:
        raise ValueError(f"no samples found for the test placements {config.TEST_PLACEMENTS}")
    if not train:
        raise ValueError("no train samples")
    return predict(build_models(train), test)


def scores(y: np.ndarray, pred: np.ndarray) -> dict:
    """Accuracy, balanced accuracy and the chance floor (= share of the majority class)."""
    chance = np.bincount(y.astype(int)).max() / len(y)
    return {"windows_n": len(y), "accuracy": accuracy_score(y, pred),
            "balanced_accuracy": balanced_accuracy_score(y, pred), "chance": chance}


def score_table(preds: list[dict], by: list[str] = ()) -> pd.DataFrame:
    """One row per model x window set (x every column in `by`, e.g. ["condition"]), pooled over samples."""
    df = pd.DataFrame(preds)
    keys = ["model", "windows", *by]
    rows = []
    for group, part in df.groupby(keys, sort=False):
        y, pred = np.concatenate(list(part.y)), np.concatenate(list(part.pred))
        rows.append({**dict(zip(keys, group)), "samples_n": len(part), **scores(y, pred)})
    return pd.DataFrame(rows)


def confusions(preds: list[dict], windows: str = "all") -> dict[str, np.ndarray]:
    """2x2 confusion matrix per model (rows = true rest/contract, columns = predicted)."""
    out = {}
    for p in preds:
        if p["windows"] != windows:
            continue
        cm = confusion_matrix(p["y"], p["pred"], labels=[config.REST, config.CONTRACT])
        out[p["model"]] = out.get(p["model"], 0) + cm
    return out


def markdown_table(df: pd.DataFrame, digits: int = 3) -> str:
    """Plain Markdown table (no extra dependency). Floats are rounded to `digits`."""
    def fmt(v):
        return f"{v:.{digits}f}" if isinstance(v, float) else str(v)
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def confusion_markdown(cms: dict[str, np.ndarray]) -> str:
    """All confusion matrices as one Markdown table: model | true | pred rest | pred contract."""
    rows = [{"model": m, "true": t, "pred rest": int(cm[i, 0]), "pred contract": int(cm[i, 1])}
            for m, cm in cms.items() for i, t in enumerate(["rest", "contract"])]
    return markdown_table(pd.DataFrame(rows))
