"""Filtering, windowing, features, clean-window selection and rest-baseline calibration.

The live app and the offline scripts use exactly the same classes (causal filter
with state + Windower), so features are identical in both.
"""

from dataclasses import dataclass

import numpy as np
from scipy import signal

from semgia import config

FEATURE_NAMES = ["rms", "mav", "wl", "zc"]


class Filter:
    """Causal filter that keeps its state between chunks.

    Raw EMG: bandpass + notch. Envelope sensor: passed through unchanged
    (a high-pass would erase a sustained contraction).
    """

    def __init__(self, fs: int = config.FS, raw: bool = config.RAW_SIGNAL):
        self.raw = raw
        if raw:
            high = min(config.BANDPASS_HZ[1], 0.45 * fs)
            bp = signal.butter(4, [config.BANDPASS_HZ[0], high], btype="bandpass", fs=fs, output="sos")
            b, a = signal.iirnotch(config.NOTCH_HZ, config.NOTCH_Q, fs=fs)
            self.sos = np.vstack([bp, signal.tf2sos(b, a)])
        self.zi = None

    def process(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        if not self.raw or len(x) == 0:
            return x
        if self.zi is None:  # start the filter at the first value -> no startup spike
            self.zi = signal.sosfilt_zi(self.sos) * x[0]
        y, self.zi = signal.sosfilt(self.sos, x, zi=self.zi)
        return y


class Windower:
    """Push filtered samples in, get complete windows out (WINDOW long, every STEP)."""

    def __init__(self, window: int = config.WINDOW, step: int = config.STEP):
        self.window = window
        self.step = step
        self.buf = np.empty(0)
        self.total = 0          # samples pushed so far
        self.next_end = window  # sample index where the next window ends

    def push(self, x: np.ndarray) -> list[tuple[int, np.ndarray]]:
        """Returns a list of (end_sample_index, window). The window covers [end - WINDOW, end)."""
        self.buf = np.concatenate([self.buf, x])[-(self.window + len(x)):]
        self.total += len(x)
        out = []
        while self.next_end <= self.total:
            start = len(self.buf) - (self.total - self.next_end) - self.window
            out.append((self.next_end, self.buf[start:start + self.window]))
            self.next_end += self.step
        return out


def features(w: np.ndarray) -> np.ndarray:
    """RMS, mean absolute value, waveform length, zero crossings of one window."""
    return np.array([
        np.sqrt(np.mean(w ** 2)),
        np.mean(np.abs(w)),
        np.sum(np.abs(np.diff(w))),
        np.sum(np.diff(np.signbit(w).astype(int)) != 0),
    ])


def clean_mask(ends: np.ndarray, change_points, n_total: int,
               trim: int = int(config.TRIM_S * config.FS), window: int = config.WINDOW) -> np.ndarray:
    """True for windows that are at least `trim` samples away from every label change,
    from the start (0) and from the end (n_total) of the recording."""
    starts = ends - window
    ok = (starts >= trim) & (ends <= n_total - trim)
    for p in change_points:
        ok &= (ends <= p - trim) | (starts >= p + trim)
    return ok


@dataclass
class Calibration:
    """Rest baseline of one sample: features are divided by it, so 1.0 = 'like rest'.

    Taken from the clean part of the first rest phase -> each sample calibrates itself,
    which cancels out electrode placement / skin contact differences.
    """
    rest: np.ndarray

    @classmethod
    def from_rest(cls, rest_feats: np.ndarray) -> "Calibration":
        if len(rest_feats) == 0:
            raise ValueError("no clean rest windows for the baseline")
        return cls(np.median(rest_feats, axis=0))

    def normalize(self, f: np.ndarray) -> np.ndarray:
        return f / np.maximum(self.rest, 1e-9)


def window_features(x: np.ndarray, fs: int = config.FS) -> tuple[np.ndarray, np.ndarray]:
    """Offline: whole signal -> (end_indices, feature matrix)."""
    pairs = Windower().push(Filter(fs).process(x))
    ends = np.array([e for e, _ in pairs], dtype=int)
    feats = np.array([features(w) for _, w in pairs]).reshape(-1, len(FEATURE_NAMES))
    return ends, feats


def sample_calibration(labels: np.ndarray, ends: np.ndarray, feats: np.ndarray) -> Calibration:
    """Rest baseline of one sample = clean windows of its first rest phase.
    This is the current per-sample calibration (per-placement calibration is planned)."""
    if labels[0] != config.REST:
        raise ValueError("a sample must start with rest (needed for the baseline)")
    changes = np.flatnonzero(np.diff(labels)) + 1
    first_change = changes[0] if len(changes) else len(labels)
    return Calibration.from_rest(feats[clean_mask(ends, [], first_change)])


def sample_dataset(df, clean_only: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """signal.csv DataFrame (columns t_s, value, label) -> normalized features X and labels y.

    clean_only=True:  only windows away from label changes (for training).
    clean_only=False: every window, labelled at its centre (realistic test incl. transitions).
    """
    labels = df["label"].to_numpy()
    ends, feats = window_features(df["value"].to_numpy())
    changes = np.flatnonzero(np.diff(labels)) + 1
    calib = sample_calibration(labels, ends, feats)
    if clean_only:
        keep = clean_mask(ends, changes, len(labels))
        y = labels[ends[keep] - 1]
    else:
        keep = np.ones(len(ends), dtype=bool)
        y = labels[ends - config.WINDOW // 2]
    return calib.normalize(feats[keep]), y
