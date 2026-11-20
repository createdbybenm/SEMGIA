"""First look at real samples: one PNG per sample, to check by eye whether our settings fit the data.

Questions it answers:
  - TRIM_S (1.5 s): does the contraction really start/stop inside the trimmed zone, i.e. are the green
    "clean" windows really in steady rest / steady contraction?
  - THRESHOLD_ON / OFF (3x / 2x rest): does RMS/rest cross them in the contraction
    and stay below them in rest?
Top:    filtered signal, contraction (timer label) shaded orange, clean windows as a green bar at the bottom.
Bottom: RMS / rest baseline per window (log scale) with the ON/OFF threshold lines.
Uses the same processing as training (Filter, window_features, clean_mask, sample_calibration).

    python scripts/first_look.py                                       # first 3 samples in data/raw
    python scripts/first_look.py --samples sample_004 sample_017 --out figures/first_look
"""

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")   # no window, only files
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from semgia import config  # noqa: E402
from semgia.processing import Filter, clean_mask, sample_calibration, window_features  # noqa: E402
from semgia.storage import list_samples, load_sample  # noqa: E402


def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """(first, last) index of every run of True in a boolean array."""
    edges = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1) - 1))


def plot_sample(sample_dir: Path, out_dir: Path) -> Path:
    df, meta = load_sample(sample_dir)
    labels, values = df["label"].to_numpy(), df["value"].to_numpy()
    t = np.arange(len(values)) / config.FS
    ends, feats = window_features(values)
    rms_ratio = sample_calibration(labels, ends, feats).normalize(feats)[:, 0]
    changes = np.flatnonzero(np.diff(labels)) + 1
    clean = clean_mask(ends, changes, len(labels))

    fig, (top, bottom) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    top.plot(t, Filter().process(values), lw=0.4, color="black")
    for a, b in runs(labels == config.CONTRACT):
        top.axvspan(t[a], t[b], color="orange", alpha=0.25, label="contract (timer)")
    for a, b in runs(clean):   # clean window a..b covers [ends[a] - WINDOW, ends[b]]
        top.axvspan((ends[a] - config.WINDOW) / config.FS, ends[b] / config.FS, ymax=0.05, color="green",
                    label="clean windows")
    handles, names = top.get_legend_handles_labels()
    unique = dict(zip(names, handles))   # one legend entry per name, not one per span
    top.legend(unique.values(), unique.keys(), loc="upper right")
    top.set_ylabel("filtered value")
    top.set_title(f"{meta['sample_id']}  {meta.get('placement_id', '')}  "
                  f"{meta.get('effort', '')}  {meta.get('condition', '')}")

    bottom.semilogy(ends / config.FS, rms_ratio, color="black", lw=1)
    bottom.axhline(config.THRESHOLD_ON, color="red", ls="--", label=f"ON {config.THRESHOLD_ON}x")
    bottom.axhline(config.THRESHOLD_OFF, color="blue", ls="--", label=f"OFF {config.THRESHOLD_OFF}x")
    for a, b in runs(labels == config.CONTRACT):
        bottom.axvspan(t[a], t[b], color="orange", alpha=0.25)
    bottom.set_ylabel("RMS / rest")
    bottom.set_xlabel("time (s)")
    bottom.legend(loc="upper right")

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{meta['sample_id']}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)
    return path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default=str(config.DATA_RAW))
    p.add_argument("--samples", nargs="*", help="sample ids (default: the first 3)")
    p.add_argument("--out", default=str(config.ROOT / "figures" / "first_look"))
    a = p.parse_args()
    dirs = list_samples(Path(a.data))
    dirs = [d for d in dirs if d.name in a.samples] if a.samples else dirs[:3]
    if not dirs:
        sys.exit(f"No (matching) samples in {a.data}")
    for d in dirs:
        print(plot_sample(d, Path(a.out)))


if __name__ == "__main__":
    main()
