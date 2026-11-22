"""Live logic of the recording app (no GUI code here, so it can be tested).

LivePredictor  runs all the time: filter -> windows -> features -> model -> smoother.
SampleRecorder records ONE 24 s sample. The label of every row is computed from the
sample counter (time = row / FS) and config.SAMPLE_STEPS - never from the PC clock or
from what the person did.
"""

import json
import logging
from pathlib import Path

import numpy as np

from semgia import config
from semgia.model import Smoother, ThresholdModel
from semgia.processing import Calibration, Filter, Windower, features
from semgia.storage import (
    OPERATOR_RE,
    PLACEMENT_RE,
    SUBJECT_RE,
    AzureUploader,
    LocalWriter,
    list_samples,
    make_metadata,
)

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


# --- Files downloaded by the web page (firmware/semgia_emg/pagina.h) ---
WEB_SAMPLE_FORMAT = "semgia-sample-1"
WEB_CALIB_FORMAT = "semgia-calib-2"
CALIB_N = sum(s for _, s in config.CALIB_STEPS) * config.FS
CHOICES = {"muscle": config.MUSCLES, "side": config.SIDES, "effort": config.EFFORTS,
           "condition": config.CONDITIONS}


def save_web_sample(payload: dict, root: Path = config.DATA_RAW, model=None,
                    upload: bool = False) -> Path | None:
    """One downloaded web sample -> data/raw/sample_NNN/, written by SampleRecorder exactly like record.py.

    The values are replayed through LivePredictor + SampleRecorder, so signal.csv (labels from the
    row number), predictions.csv and the optional Azure upload are identical to a live recording.
    Returns the new folder, or None if this recording (same placement + start_time_utc) was already
    imported. Raises ValueError if the file is incomplete or the metadata is wrong.
    upload=True also sends it to Azure (best effort, never raises; needs the .env connection string).
    """
    if payload.get("format") != WEB_SAMPLE_FORMAT:
        raise ValueError(f"not a web sample (format {payload.get('format')!r})")
    fields = {k: v for k, v in payload["metadata"].items() if k != "sample_id"}
    values = np.asarray(payload["values"], dtype=float)
    if len(values) != SAMPLE_N:
        raise ValueError(f"sample has {len(values)} rows, expected {SAMPLE_N} (aborted?)")
    adc_max = 2 ** config.ADC_BITS - 1
    if values.min() < 0 or values.max() > adc_max:
        raise ValueError(f"values outside 0..{adc_max}: not raw ADC counts (old web page / firmware?)")
    if int(fields.get("sampling_rate_hz", 0)) != config.FS:
        raise ValueError(f"sampling_rate_hz {fields.get('sampling_rate_hz')} != config.FS {config.FS}")
    for key, allowed in CHOICES.items():
        if fields.get(key) not in allowed:
            raise ValueError(f"{key}={fields.get(key)!r} is not one of {allowed} (web page out of date?)")
    for d in list_samples(root):
        old = json.loads((d / "metadata.json").read_text())
        if (old.get("start_time_utc"), old.get("placement_id")) == (fields.get("start_time_utc"),
                                                                    fields.get("placement_id")):
            return None
    meta = make_metadata(root=root, **fields)   # privacy gate: P001 / OP01 / E01
    predictor = LivePredictor(model or ThresholdModel())
    rec = SampleRecorder(meta, predictor.total, root, AzureUploader(meta, conn_str=None if upload else ""))
    for start in range(0, SAMPLE_N, config.STEP):   # same chunking as a live stream
        x = values[start:start + config.STEP]
        rec.push(x, predictor.push(x))
        if rec.calib is not None:
            predictor.calib = rec.calib
    rec.close()
    return rec.writer.dir


def save_web_calibration(payload: dict, root: Path = config.DATA_RAW) -> Path | None:
    """One downloaded web calibration -> data/raw/calibration_EXX/{calibration.json, calibration.csv}.

    calibration.csv = t_s,value,step. step comes from the timer (config.CALIB_STEPS: 0 prepare, 1 rest,
    2 max contraction), like the sample labels - never from the file. rest_rms / max_rms = what the page
    computed (RMS of 200 ms windows minus their mean, in ADC counts).
    Returns None if this calibration was already imported. Raises ValueError if the placement
    already has a different calibration (delete the folder by hand to replace it).
    """
    if payload.get("format") != WEB_CALIB_FORMAT:
        raise ValueError(f"not a web calibration (format {payload.get('format')!r})")
    id_rules = (("subject_id", SUBJECT_RE), ("operator_id", OPERATOR_RE), ("placement_id", PLACEMENT_RE))
    for key, regex in id_rules:
        if not regex.match(str(payload.get(key, ""))):
            raise ValueError(f"bad {key} {payload.get(key)!r} (pseudonyms only: P001 / OP01 / E01)")
    if int(payload.get("sampling_rate_hz", 0)) != config.FS:
        raise ValueError(f"sampling_rate_hz {payload.get('sampling_rate_hz')} != config.FS {config.FS}")
    values = np.asarray(payload["values"], dtype=float)
    if len(values) != CALIB_N:
        raise ValueError(f"calibration has {len(values)} rows, expected {CALIB_N} (aborted?)")
    adc_max = 2 ** config.ADC_BITS - 1
    if values.min() < 0 or values.max() > adc_max:
        raise ValueError(f"values outside 0..{adc_max}: not raw ADC counts")
    steps = np.concatenate([np.full(s * config.FS, st) for st, s in config.CALIB_STEPS])
    info = {k: payload[k] for k in ("placement_id", "subject_id", "operator_id", "start_time_utc",
                                    "sampling_rate_hz", "rest_rms", "max_rms")}
    folder = Path(root) / f"calibration_{info['placement_id']}"
    if folder.exists():
        old = json.loads((folder / "calibration.json").read_text())
        if old.get("start_time_utc") == info["start_time_utc"]:
            return None
        raise ValueError(f"{folder} already exists (another calibration of this placement). "
                         "Delete it by hand to replace it, or use a new placement ID.")
    folder.mkdir(parents=True)
    (folder / "calibration.json").write_text(json.dumps(info, indent=2))
    with open(folder / "calibration.csv", "w") as f:
        f.write("t_s,value,step\n")
        for i, (v, s) in enumerate(zip(values, steps)):
            f.write(f"{i / config.FS:.3f},{int(v)},{int(s)}\n")
    return folder
