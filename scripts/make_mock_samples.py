"""Generate fake samples (instantly, not in real time) so train/evaluate work without a sensor.

    python scripts/make_mock_samples.py                    # 5 placements x 10 samples -> data/synthetic/
"""

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from semgia import config  # noqa: E402
from semgia.recorder import SAMPLE_N, label_at  # noqa: E402
from semgia.sources import MockSource  # noqa: E402
from semgia.storage import LocalWriter, make_metadata  # noqa: E402

EFFORT_GAIN = {"light": 0.4, "medium": 0.7, "strong": 1.0}


def make_sample(out: Path, placement: int, rng: np.random.Generator,
                effort: str = "medium", condition: str = "fresh") -> Path:
    gain = rng.uniform(0.5, 2.0) * EFFORT_GAIN[effort]   # placement + effort change the amplitude
    meta = make_metadata(root=out, subject_id=config.PATIENT_ID, operator_id="OP00",
                         placement_id=f"E{placement:02d}",
                         sensor_id="mock", effort=effort, condition=condition, notes="synthetic")
    shutil.rmtree(out / meta["sample_id"], ignore_errors=True)
    writer = LocalWriter(meta, out)
    src = MockSource(gain=gain, fatigue=1.0 if condition == "fatigued" else 0.0, seed=int(rng.integers(1e9)))
    labels = label_at(np.arange(SAMPLE_N))
    changes = np.flatnonzero(np.diff(labels)) + 1
    for seg_labels in np.split(labels, changes):
        src.set_cue(int(seg_labels[0]))
        writer.write_samples(src.generate(len(seg_labels)), seg_labels)
    writer.close()
    return writer.dir


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--placements", type=int, default=5)
    p.add_argument("--per-placement", type=int, default=10)
    p.add_argument("--out", default=str(config.DATA_SYNTHETIC))
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    out = Path(a.out)
    shutil.rmtree(out, ignore_errors=True)  # synthetic data is disposable
    rng = np.random.default_rng(a.seed)
    for e in range(1, a.placements + 1):
        for i in range(a.per_placement):
            effort = config.EFFORTS[i % len(config.EFFORTS)]
            condition = "fatigued" if i >= a.per_placement - 2 else "fresh"
            make_sample(out, e, rng, effort, condition)
    print(f"wrote {a.placements * a.per_placement} samples to {out}")


if __name__ == "__main__":
    main()
