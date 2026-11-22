# scripts/ – command line tools (thin wrappers around semgia/)

| Script | Does | Example |
|---|---|---|
| `record.py` | recording app: live plot + AI, "Collect sample" button, metadata form, 24 s cues | `python scripts/record.py --source mock` |
| `import_web.py` | web-interface downloads (`semgia_*.json`) → `data/raw/sample_NNN/`, `calibration_EXX/` | `python scripts/import_web.py` |
| `make_mock_samples.py` | fake samples instantly → `data/synthetic/` (5 placements × 10) | `python scripts/make_mock_samples.py` |
| `train.py` | clean windows of all **train** samples → `models/model.joblib` (`--kind logreg\|lda\|forest`) | `python scripts/train.py --data data/synthetic` |
| `evaluate.py` | leave-one-placement-out on train placements: threshold floor vs. logreg/lda/forest; `--final` = test once; `--out x.md` | `python scripts/evaluate.py` |
| `export_metadata.py` | `data/metadata.csv` (course columns + `file_name` + our fields) | `python scripts/export_metadata.py` |
| `check_quality.py` | quality rule → `QUALITY-REPORT.md` (train/evaluate skip rejected samples) | `python scripts/check_quality.py` |
| `first_look.py` | one PNG per sample → `figures/first_look/`: check TRIM_S and thresholds by eye | `python scripts/first_look.py --samples sample_001` |
| `upload_sample.py` | push offline-recorded samples to Azure | `python scripts/upload_sample.py data/raw/sample_007` |

## record.py
- **Backup/demo only.** The real recording happens in the ESP32 web page (`firmware/HamShot_EMG/`). Keep record.py working and
  in line with the same file format, but don't add big features here.
- GUI: tkinter + embedded matplotlib. `App` holds the logic (`tick()` = read → predict → record),
  `run_gui()` only displays it. `--no-gui` runs the same `App` headless (used for testing). Keep it that way.
- Flags: `--source mock|serial|file`, `--port COM3`, `--model threshold|ml`, `--no-upload`, `--font-scale 2`,
  headless: `--no-gui --count 3 --subject P001 --operator OP01 --placement-id E01`.
- The form is pre-filled from the newest sample's metadata.json. Dropdown choices come from `config.py`.
- Predictions need a rest baseline → nothing is shown before second 8 of the first sample.
- Subject screen: big cue + "Sample 4 of 10 · E01" (`config.SAMPLES_PER_PLACEMENT`) + a beep at start, each switch, end.
- **Demo fallback:** `--source file --file data/raw/sample_NNN/signal.csv` replays a recording. "Collect sample"
  rewinds the file so the cues match it; output goes to `data/demo/` (gitignored), never `data/raw/`, no upload.

## Rules
- Scripts import from `semgia`. No signal-processing logic in here.
- Each script starts with a docstring showing how to run it. Keep it up to date.
- Every script must work with mock data (no hardware, no Azure).
- `evaluate.py --final` opens the test set. Run it once, at the end. Never commit outputs made from `data/synthetic`.
