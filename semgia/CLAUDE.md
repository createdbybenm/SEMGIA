# semgia/ – the core package

| File | What | Owner |
|---|---|---|
| `config.py` | ALL constants (FS, windows, SAMPLE_STEPS, TRIM_S, thresholds, dropdown choices, Azure names, paths) | everyone |
| `sources.py` | `MockSource`, `FileSource`, `SerialSource` | Hardware |
| `processing.py` | `Filter`, `Windower`, `features`, `clean_mask`, `Calibration`, `sample_calibration`, `sample_dataset` | AI |
| `model.py` | `ThresholdModel`, `MLModel("logreg"/"lda"/"forest")`, `ML_KINDS` (compared kinds), `Smoother` | AI |
| `evaluation.py` | fair split (`split_train_test`), `lopo_predictions`, `final_predictions`, scores, confusion, Markdown | AI |
| `report.py` | `data/metadata.csv` rows (`metadata_table`), quality rule (`check_signal`) for `QUALITY-REPORT.md` | AI |
| `recorder.py` | `label_at`, `LivePredictor`, `SampleRecorder` (live logic of the app, no GUI) | App |
| `storage.py` | `make_metadata`, `next_sample_id`, `LocalWriter`, `AzureUploader`, `load_sample`, `upload_sample`, `delete_sample` | Azure |

## Frozen interfaces
The list is in the root `CLAUDE.md` (Hard rules). Change one only after team agreement + a MEMORY.md line.

## How a sample becomes training data (`sample_dataset`)
1. Whole 24 s signal → 200 ms windows every 100 ms → subtract window mean (ESP32 offset) → 4 features per window.
   Before that, `Filter` notches 60 Hz + harmonics (causal, with state; the sensor has no notch).
2. Baseline = median features of the clean windows in the first rest phase → divide all features by it.
3. `clean_mask`: keep windows ≥ `TRIM_S` from every label change and from start/end → middle 5 s of each phase.
4. Label of a window = the timer label (from the CSV). `clean_only=False` gives every window (for realistic testing).

## Calibration: two copies of the rest baseline
Today every sample calibrates itself on the clean part of its first rest phase. That rule exists **twice**:
- offline: `processing.sample_calibration` (used by `sample_dataset` and `scripts/first_look.py`);
- live: `recorder.SampleRecorder.push` collects the rest windows itself and builds the `Calibration`, then the caller
  hands it to `LivePredictor.calib` (`recorder.save_web_sample`, `scripts/record.py`, the tests).
Change one → change both, and keep `TRIM_S` the same in each. Per-placement calibration (rest + max once per
placement) was agreed but is not built (MEMORY.md 2026-11-24).

## Rules
- `processing.py` is used live AND offline: chunked processing == whole-signal processing (there's a test for this).
  `Filter` must stay causal with state (`sosfilt` + `zi`), one instance per recording.
- `features` subtracts the window mean only for raw EMG (`RAW_SIGNAL = True`); for an envelope it would erase a
  sustained contraction.
- Models always get **normalized** features (÷ rest baseline). Never raw amplitudes.
- Labels come from `recorder.label_at` (timer). Never derive labels from the signal.
- `storage.LocalWriter` refuses to overwrite an existing sample folder (on purpose).
- `storage.AzureUploader` must catch every exception and only log. A broken Wi-Fi must never stop a recording.
- `make_metadata` is the privacy gate. Don't bypass it, and don't add free-text fields that invite names.
- Azure SDK imports stay inside functions, so the package works without Azure.
- New features/models: add them next to the existing ones (new model kind → `ML_KINDS`), compare with `scripts/evaluate.py`,
  and only switch the default if leave-one-placement-out gets better. Write the result into MEMORY.md.
