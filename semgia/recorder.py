"""Live logic of the recording app (no GUI code here, so it can be tested).

LivePredictor  runs all the time: filter -> windows -> features -> model -> smoother.
SampleRecorder records ONE 24 s sample. The label of every row is computed from the
sample counter (time = row / FS) and config.SAMPLE_STEPS - never from the PC clock or
from what the person did.
"""

import logging

import numpy as np

from semgia import config
from semgia.model import Smoother
from semgia.processing import Calibration, Filter, Windower, features
from semgia.storage import AzureUploader, LocalWriter

log = logging.getLogger(__name__)

# sample index where each phase ends: [8000, 16000, 24000]
PHASE_ENDS = np.cumsum([int(d * config.FS) for _, d in config.SAMPLE_STEPS])
PHASE_LABELS = np.array([lab for lab, _ in config.SAMPLE_STEPS])
SAMPLE_N = int(PHASE_ENDS[-1])
FIRST_CHANGE = int(PHASE_ENDS[0])
TRIM = int(config.TRIM_S * config.FS)


def label_at(i: np.ndarray) -> np.ndarray:
    """Label (0/1) for row indices i of a sample."""
    return PHASE_LABELS[np.minimum(np.searchsorted(PHASE_ENDS, i, side="right"), len(PHASE_ENDS) - 1)]


def phase_at(i: int) -> tuple[int, float]:
    """(label, seconds left in this phase) at row i - for the on-screen cue."""
    k = min(int(np.searchsorted(PHASE_ENDS, i, side="right")), len(PHASE_ENDS) - 1)
    return int(PHASE_LABELS[k]), max(PHASE_ENDS[k] - i, 0) / config.FS


class LivePredictor:
    """Continuous prediction. Needs a Calibration (rest baseline) before it predicts anything."""

    def __init__(self, model):
        self.model = model
        self.filter, self.windower, self.smooth = Filter(), Windower(), Smoother()
        self.calib: Calibration | None = None
        self.total = 0  # samples pushed so far
        self.pred: int | None = None
        self.filtered = np.empty(0)

    def push(self, x: np.ndarray) -> list[tuple[int, np.ndarray, int | None]]:
        """Returns (end_index, features, prediction or None) for every new window."""
        self.total += len(x)
        self.filtered = self.filter.process(x)  # kept for the live plot
        out = []
        for end, w in self.windower.push(self.filtered):
            f = features(w)
            if self.calib is not None:
                self.pred = self.smooth(self.model.predict(self.calib.normalize(f)))
            out.append((end, f, self.pred))
        return out


class SampleRecorder:
    """Records one sample. Create it, then call push() with every chunk until .done."""

    def __init__(self, meta: dict, start_index: int, root=config.DATA_RAW,
                 uploader: AzureUploader | None = None):
        self.meta = meta
        self.start = start_index          # LivePredictor.total when recording started
        self.writer = LocalWriter(meta, root)
        self.uploader = uploader or AzureUploader(meta, conn_str="")
        self.n = 0                        # rows written
        self.rest_feats: list[np.ndarray] = []
        self.calib: Calibration | None = None
        self.chunk_vals, self.chunk_preds, self.seq = [], [], 0

    @property
    def done(self) -> bool:
        return self.n >= SAMPLE_N

    def cue(self) -> tuple[int, float]:
        return phase_at(self.n)

    def push(self, x: np.ndarray, windows: list[tuple[int, np.ndarray, int | None]]) -> None:
        x = x[:SAMPLE_N - self.n]                       # stop exactly at 24 s
        self.writer.write_samples(x, label_at(self.n + np.arange(len(x))))
        for end, f, pred in windows:
            rel = end - self.start                      # window end inside this sample
            if not 0 < rel <= SAMPLE_N:
                continue
            if rel - config.WINDOW >= TRIM and rel <= FIRST_CHANGE - TRIM:
                self.rest_feats.append(f)               # clean part of the first rest -> baseline
            if pred is not None:
                self.writer.write_prediction(rel / config.FS, pred)
                self.chunk_preds.append(pred)
        self.n += len(x)
        if self.calib is None and self.n >= FIRST_CHANGE and self.rest_feats:
            self.calib = Calibration.from_rest(np.array(self.rest_feats))
            log.info("Rest baseline: %s", self.calib.rest)

        self.chunk_vals.extend(x)
        if len(self.chunk_vals) >= config.UPLOAD_EVERY_S * config.FS or (self.done and self.chunk_vals):
            t0 = (self.n - len(self.chunk_vals)) / config.FS
            self.uploader.send(self.seq, t0, self.chunk_vals, self.chunk_preds)
            self.seq += 1
            self.chunk_vals, self.chunk_preds = [], []

    def close(self) -> None:
        self.writer.close()
        self.uploader.close()
