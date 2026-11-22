# Architecture

> **Recording** happens in the web page served by the EMG ESP32 (`firmware/HamShot_EMG/`, wiring in `firmware/CLAUDE.md`), adapted to write exactly the
> files described below. `scripts/record.py` implements the same flow in Python as a backup/demo.

```
 ┌──────────┐  analog  ┌──────────────┐  USB serial "<int>\n" @ 1 kHz
 │EMG sensor├─────────►│ ESP32 12-bit ├──────────────────────────────┐
 └──────────┘          └──────────────┘                              │
                                                                     ▼
 LOCAL – web interface (recording)  /  scripts/record.py (backup) + semgia/ (AI) ────
   always:  Source.read() → Windower (200 ms / 100 ms) → features (− window mean; RMS, MAV, WL, ZC)
            → ÷ rest baseline → Model.predict → Smoother → "REST" / "CONTRACTION" + live plot
   button "Collect sample" → metadata form → SampleRecorder (24 s):
            label from timer → data/raw/sample_NNN/{metadata.json, signal.csv, predictions.csv}
            └─► AzureUploader (background thread, every 2 s, never raises)
 ────────────────────────────────────────────┼────────────────────────────────────────
 AZURE (EU region, resource group rg-semgia) ▼
   Storage Account
     Blob   signals/<sample_id>/metadata.json, <seq>.csv   (raw values, 2 s per file)
     Table  samples      PK="sample", RK=sample_id, all metadata fields
     Table  predictions  PK=sample_id, RK=seq, t0_s, n, contract_ratio, labels
   App Service  ── dashboard/app.py (Streamlit, read-only, polls every 3 s)
```

## Calibration (agreed target – not implemented yet)
Once per patient + electrode placement, with the web interface's existing sequence: rest, then max contraction.
→ rest level = 0, max contraction = 1 for **all samples of that placement**.
Why: in live use you calibrate once after putting the electrodes on, then the AI simply runs.
Calibration only removes nuisance variation (electrode gain, skin contact). Rest vs. contraction, effort and
fatigue stay fully visible, so the AI still learns them. `evaluate.py` will compare calibrated vs. raw features.
**Current code:** still uses each sample's own first rest phase as baseline (shown below as "baseline").

## One sample (24 s, continuous)
```
time   0 s ──────── 8 s ──────── 16 s ──────── 24 s
screen   REST 8 s   │ CONTRACT 8 s │   REST 8 s
label    0 0 0 0 0  │ 1 1 1 1 1 1  │ 0 0 0 0 0      ← from the timer only (row / 1000 Hz)
clean     [1.5–6.5] │  [9.5–14.5]  │ [17.5–22.5]    ← used for training (TRIM_S = 1.5 s)
baseline  [1.5–6.5]                                 ← rest level of this sample
```
- The CSV keeps everything. "Clean" is decided in code (`processing.clean_mask`), so the trim can be changed later.
- The first rest phase is the **baseline**: all features are divided by it (1.0 = "like rest").
  New electrodes / skin contact change the amplitude, and the baseline cancels that out.

## Why it's robust
- Electrode re-placement → calibration once per placement (target; code: per-sample rest baseline for now).
- Fatigue → amplitude up, frequency down → ratio features + `fatigued` samples in the training data.
- Reaction time / slow ramps → the transitions are excluded from training (clean windows only).
- Flickering → hysteresis (threshold model) + majority-vote smoothing.

## Models (why logistic regression?)
2 classes, 4 numbers per window, ~100 samples → a simple model generalizes best to new electrode placements,
is explainable (weights per feature) and trains in < 1 s. Neural networks need far more data.
It is not fixed: evaluate.py compares the models below and real data decides (sources: `docs/report/model_research.md`).

- **A – ThresholdModel:** RMS > 3× rest → contraction, < 2× rest → rest. No training needed. Fallback.
- **B – MLModel("logreg"):** log → StandardScaler → LogisticRegression on the 4 features (`models/model.joblib`).
- **MLModel("lda"):** linear discriminant analysis, same input, equal priors. Linear cross-check of logreg.
- **MLModel("forest"):** random forest, same input. Non-linear comparison only.
- Class imbalance (rest 16 s : contraction 8 s): class weights (`class_weight="balanced"`, LDA `priors=[0.5, 0.5]`),
  no resampling. The list of compared kinds is `ML_KINDS` in `semgia/model.py`.
- **Fair split (course rule, implemented):** the test placements are `TEST_PLACEMENTS` in `config.py` (only place;
  `set` column in `data/metadata.csv`). `evaluate.py` (default) runs leave-one-placement-out on the **train**
  placements only, to choose features + model. `evaluate.py --final` trains on all train placements and scores the
  test placements **once**. `train.py` never uses test placements.
- Scores per model: accuracy + balanced accuracy on clean, all and smoothed windows (smoothed = all windows through
  `Smoother`, like the app), next to the chance floor (majority class share) and the threshold floor; split by
  `condition` (fresh/fatigued) and placement; confusion matrix on all windows. `--out file.md` writes the tables.
- Rejected samples (`QUALITY-REPORT.md`, `scripts/check_quality.py`) are skipped by train + evaluate.

## Filters
All filtering is **analog** (front end): band-pass 20–447 Hz + 60 Hz notch (Mexico mains). **No digital filter**
(Ben, 2026-11-19); `processing.Filter` is a pass-through that only keeps one interface for live and offline code.
Software removes the ESP32 offset (rest ≈ 2048 of 0..4095) by subtracting each window's mean in `features`
(not for an envelope sensor, `RAW_SIGNAL = False`). Document the analog filters in PROTOCOL.md (P1).

## File formats
- `signal.csv`: `t_s,value,label` – one row per reading (24 000 rows).
- `predictions.csv`: `t_s,prediction` – one row per 100 ms (as soon as a baseline exists).
- `metadata.json`: `sample_id, placement_id, subject_id, operator_id, muscle, side, sensor_id, electrode_type,
  placement_notes, effort, condition, sampling_rate_hz, start_time_utc, notes`.
- `data/metadata.csv` (course requirement, written by `scripts/export_metadata.py` from the JSON files + per-session
  constants in `config.py`): one row per recording, see `docs/course/requirements.md`.
