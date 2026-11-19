# Architecture

> **Recording** will happen in our existing web interface (separate repo, Windows 11), adapted to write exactly the
> files described below. `scripts/record.py` implements the same flow in Python as a backup/demo.

```
 ┌──────────┐  analog  ┌──────────────┐  USB serial "<int>\n" @ 1 kHz
 │EMG sensor├─────────►│ Arduino (A0) ├──────────────────────────────┐
 └──────────┘          └──────────────┘                              │
                                                                     ▼
 LOCAL – web interface (recording)  /  scripts/record.py (backup) + semgia/ (AI) ────
   always:  Source.read() → Filter → Windower (200 ms / 100 ms) → features (RMS, MAV, WL, ZC)
            → ÷ rest baseline → Model.predict → Smoother → "AI says: ..." + live plot
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
It is not fixed: evaluate.py compares all three below and real data decides.

- **A – ThresholdModel:** RMS > 3× rest → contraction, < 2× rest → rest. No training needed. Fallback.
- **B – MLModel("logreg"):** log → StandardScaler → LogisticRegression on the 4 features (`models/model.joblib`).
- **MLModel("forest"):** random forest, same input. Comparison only.
- `scripts/evaluate.py`: leave-one-placement-out, balanced accuracy, on clean windows and on all windows.

## File formats
- `signal.csv`: `t_s,value,label` – one row per reading (24 000 rows).
- `predictions.csv`: `t_s,prediction` – one row per 100 ms (as soon as a baseline exists).
- `metadata.json`: `sample_id, placement_id, subject_id, operator_id, muscle, side, sensor_id, electrode_type,
  placement_notes, effort, condition, sampling_rate_hz, start_time_utc, notes`.
