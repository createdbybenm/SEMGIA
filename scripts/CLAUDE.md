# scripts/ – command line tools (thin wrappers around semgia/)

| Script | Does | Example |
|---|---|---|
| `record.py` | recording app: live plot + AI, "Collect sample" button, metadata form, 24 s cues | `python scripts/record.py --source mock` |
| `make_mock_samples.py` | fake samples instantly → `data/synthetic/` (5 placements × 10) | `python scripts/make_mock_samples.py` |
| `train.py` | clean windows of all samples → `models/model.joblib` | `python scripts/train.py --data data/synthetic` |
| `evaluate.py` | leave-one-placement-out: threshold vs. logreg vs. forest, clean + all windows | `python scripts/evaluate.py` |
| `upload_sample.py` | push offline-recorded samples to Azure | `python scripts/upload_sample.py data/raw/sample_007` |

## record.py
- **Backup/demo only.** The real recording happens in our web interface (separate repo). Keep record.py working and
  in line with the same file format, but don't add big features here.
- GUI: tkinter + embedded matplotlib. `App` holds the logic (`tick()` = read → predict → record),
  `run_gui()` only displays it. `--no-gui` runs the same `App` headless (used for testing). Keep it that way.
- Flags: `--source mock|serial|file`, `--port COM3`, `--model threshold|ml`, `--no-upload`, `--font-scale 2`,
  headless: `--no-gui --count 3 --subject P001 --operator OP01 --placement-id E01`.
- The form is pre-filled from the newest sample's metadata.json. Dropdown choices come from `config.py`.
- Predictions need a rest baseline → nothing is shown before second 8 of the first sample.

## Rules
- Scripts import from `semgia`. No signal-processing logic in here.
- Each script starts with a docstring showing how to run it. Keep it up to date.
- Every script must work with mock data (no hardware, no Azure).
