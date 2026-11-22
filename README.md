# SEMGIA – sEMG contraction detection

One person, one muscle: a model decides from a single surface-EMG channel whether the right hamstrings are
**contracting or at rest**, every 100 ms. It has to stay right on new electrode placements (goal > 75 % on sessions it
never saw). The model runs on the laptop; each recording is saved with its metadata in Azure.

## Team
| Member code | GitHub user | Role | AI tool |
|---|---|---|---|
| M01 | Silver0-sys | P1 Hardware & recordings | Claude Code (VS Code) |
| M02 | createdbybenm | P2 AI | Claude Code (herdr terminal) |
| M03 | CarlosOVa | P1 Hardware & recordings | Claude Code (VS Code) |
| M04 | Ximenaabreugg | P3 Azure & privacy | Claude Code (VS Code) |

## Report 1: the data stage

### 1 Data acquisition
59 recordings = 59 trials, 6 sessions (E01–E06), 1 day (2026-11-21). 2 persons were recorded: P001 only in E01
(9 recordings, not used, see part 5), P002 in E02–E06 (50 recordings). P002 is the patient of this project.
Sensor DFRobot SEN0240 with dry electrodes built into the board (electrode distance not recorded), gain 1000,
on the right hamstrings. ESP32 12-bit ADC (0..4095), 1000 samples per second, 24 000 samples per recording.
The sensor gives the raw signal, not an envelope.
Evidence: `data/raw/sample_*/signal.csv`, `data/metadata.csv` columns `subject_id, muscle, side, sensor_model, gain,
fs_hz, adc_bits, electrode_type`.

### 2 Task
Contract the right hamstrings and hold the contraction, then relax. Two classes: contraction (1) and rest (0).
Effort per recording is light, medium or strong; the last 2 of a session are recorded fatigued.
Evidence: `data/metadata.csv` columns `muscle, side, effort, condition`; `PROTOCOL.md`.

### 3 Trial and cue timing
Rest 8 s, warning 0 s, contraction 8 s, rest 8 s = 24 s. One trial per recording. The person follows the
full-screen cue of our web page (green REPOSO / red ¡CONTRAIGA! + beep at every change). Labels come only from the
timer (row number / 1000 Hz), never from the signal. Rest is 16 s and contraction 8 s per trial, so the model uses
class weights to balance the two classes. For training we only use windows at least 1.5 s away from a cue change.
Evidence: `data/metadata.csv` columns `rest_s, warning_s, move_s, between_s`; `label` column in every `signal.csv`;
`cue/` (cue video).

### 4 Sessions
6 sessions on 1 day, new electrodes in every session (session = one electrode placement, E01 … E06).
About 10 recordings per session: 9 (E01), 10 (E02–E06).
Evidence: `data/metadata.csv` columns `session, date, start_time_utc`; `figures/` (one electrode photo per session).

### 5 Cleaning
Filters, in order (details and sources in `PROTOCOL.md`): analog band-pass 20–500 Hz on the sensor board, digital
60 Hz notch (and its harmonics), mean of each 200 ms window subtracted.
Rejection rule, fixed before any model score: a recording is rejected if a value sits at the ADC limit (0 or 4095),
if a value or row is missing, if its length is off by more than 2 %, or if it is not from the patient P002.
**26 of 59 rejected**: 9 other person (E01), 17 values at the ADC limit (E02: 5, E03: 1, E04: 3, E05: 8).
Rejected recordings stay in `data/raw/` untouched.
Evidence: `QUALITY-REPORT.md`, `scripts/check_quality.py`, `semgia/report.py`.

### 6 Fair split
Train: sessions E02–E05 (40 recordings, 23 kept). Test: session E06 (10 recordings, 10 kept). E01 is in neither
(other person). No session is in both sets, so no window of one recording is on both sides. Features and model are
chosen with leave-one-session-out on the train sessions only; the test session is opened once, at the end.
Limits of the claim: one person, one muscle, one day, 33 usable recordings, dry electrodes; it says nothing about
other people or other days.
Evidence: `data/metadata.csv` column `set`; `TEST_PLACEMENTS` in `semgia/config.py`; `docs/report/results_train.md`.

## Repository
| Path | Content |
|---|---|
| `PROTOCOL.md`, `DECISIONS.md`, `QUALITY-REPORT.md` | method + filters, decisions 7–9, rejected recordings |
| `data/raw/`, `data/metadata.csv` | every recording (untouched), one metadata row per recording |
| `rationale/`, `ai-tools/` | one file per member (named by member code) |
| `cue/`, `figures/` | cue video, electrode photo per session |
| `semgia/` | core package: sources, filter, features, models, storage |
| `scripts/` | import, train, evaluate, quality check, metadata export, recording backup app |
| `firmware/` | ESP32 firmware + recording web page |
| `dashboard/` | Streamlit dashboard (Azure App Service) |
| `docs/` | architecture, recording how-to, privacy, Azure setup, Git workflow, tasks, course assignment |
| `tests/` | pytest |

## Developer quickstart
```
git clone https://github.com/createdbybenm/SEMGIA.git && cd SEMGIA
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/check_quality.py && python scripts/export_metadata.py   # QUALITY-REPORT.md, data/metadata.csv
python scripts/evaluate.py                             # leave-one-session-out on the train sessions
python scripts/train.py --kind logreg                  # -> models/model.joblib
streamlit run dashboard/app.py                         # dashboard (local mode)
```
New recordings: the ESP32 web page downloads `semgia_*.json` files → `python scripts/import_web.py`
(`--upload` also sends them to Azure, needs `.env`, see `docs/azure_setup.md`).
Without hardware: `python scripts/make_mock_samples.py` and `python scripts/record.py --source mock`.
How it works: [docs/architecture.md](docs/architecture.md). Team workflow: [CONTRIBUTING.md](CONTRIBUTING.md).
AI assistants: [CLAUDE.md](CLAUDE.md) + [MEMORY.md](MEMORY.md).
