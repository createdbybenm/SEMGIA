"""Train Model B on the clean windows of all TRAIN samples (not TEST_PLACEMENTS) -> models/model.joblib.

    python scripts/train.py                       # real data in data/raw
    python scripts/train.py --data data/synthetic --kind forest
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from semgia import config  # noqa: E402
from semgia.evaluation import split_train_test  # noqa: E402
from semgia.model import MLModel  # noqa: E402
from semgia.processing import sample_dataset  # noqa: E402
from semgia.report import check_signal  # noqa: E402
from semgia.storage import list_samples, load_sample  # noqa: E402


def load_all(data: Path) -> list[dict]:
    """One dict per sample: id, placement, condition, effort,
    X/y (clean windows) and X_all/y_all (every window).
    Samples that fail the quality rule (QUALITY-REPORT.md) are skipped."""
    out = []
    for d in list_samples(data):
        df, meta = load_sample(d)
        reason = check_signal(df)
        if reason:
            print(f"skip {meta['sample_id']} (rejected: {reason})")
            continue
        X, y = sample_dataset(df, clean_only=True)
        X_all, y_all = sample_dataset(df, clean_only=False)
        out.append({"id": meta["sample_id"], "placement": meta["placement_id"],
                    "condition": meta.get("condition", ""), "effort": meta.get("effort", ""),
                    "X": X, "y": y, "X_all": X_all, "y_all": y_all})
    if not out:
        sys.exit(f"No samples found in {data}")
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default=str(config.DATA_RAW))
    p.add_argument("--kind", choices=["logreg", "forest"], default="logreg")
    p.add_argument("--out", default=str(config.MODELS / "model.joblib"))
    a = p.parse_args()
    samples, test = split_train_test(load_all(Path(a.data)))   # test placements never go into the model
    if test:
        print(f"not used for training (test placements {config.TEST_PLACEMENTS}): {len(test)} samples")
    if not samples:
        sys.exit("No train samples (all placements are in config.TEST_PLACEMENTS)")
    X =np.vstack([s["X"] for s in samples])
    y = np.concatenate([s["y"] for s in samples])
    MLModel(a.kind).fit(X, y).save(Path(a.out))
    print(f"Trained {a.kind} on {len(samples)} samples, {len(y)} clean windows -> {a.out}")


if __name__ == "__main__":
    main()
