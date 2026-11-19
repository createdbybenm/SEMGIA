"""Leave-one-placement-out evaluation: threshold vs. logistic regression vs. random forest.

Train on all electrode placements except one, test on the held-out placement
(= "electrodes were re-applied"). Score = balanced accuracy (rest is 2/3 of every sample,
so plain accuracy would look too good).
  clean: only the clean middle of each phase (what we trained on)
  all:   every window incl. transitions (what the live app really sees)

    python scripts/evaluate.py --data data/synthetic
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import balanced_accuracy_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from semgia import config  # noqa: E402
from semgia.model import MLModel, ThresholdModel  # noqa: E402
from train import load_all  # noqa: E402

MODELS = ["threshold", "logreg", "forest"]


def score(model, samples: list[dict], key: str) -> float:
    """Balanced accuracy over the test samples (each sample predicted separately, like live)."""
    y = np.concatenate([s["y" + key] for s in samples])
    pred = np.concatenate([model.predict_many(s["X" + key]) for s in samples])
    return balanced_accuracy_score(y, pred)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default=str(config.DATA_RAW))
    a = p.parse_args()
    samples = load_all(Path(a.data))
    placements = sorted({s["placement"] for s in samples})
    if len(placements) < 2:
        sys.exit("Need at least 2 electrode placements (E01, E02, ...) for leave-one-placement-out")

    cols = [f"{m} {k}" for m in MODELS for k in ("clean", "all")]
    print(f"{'held out':<10}{'n':>4}" + "".join(f"{c:>17}" for c in cols))
    results = []
    for held in placements:
        test = [s for s in samples if s["placement"] == held]
        train = [s for s in samples if s["placement"] != held]
        X = np.vstack([s["X"] for s in train])
        y = np.concatenate([s["y"] for s in train])
        models = [ThresholdModel(), MLModel("logreg").fit(X, y), MLModel("forest").fit(X, y)]
        row = [score(m, test, k) for m in models for k in ("", "_all")]
        results.append(row)
        print(f"{held:<10}{len(test):>4}" + "".join(f"{v:>17.3f}" for v in row))
    print(f"{'MEAN':<14}" + "".join(f"{v:>17.3f}" for v in np.mean(results, axis=0)))


if __name__ == "__main__":
    main()
