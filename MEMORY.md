# Team memory (shared, in Git)

One line per entry, newest first within a section, always dated (YYYY-MM-DD) + initials.
Add entries in the same PR as the change. Delete lines that are no longer true. Keep it < 150 lines.

## Decisions
- 2026-11-21 – **One ESP32 does everything: `firmware/semgia_emg/`** (no station, no ESP-NOW; unrelated to the
  HamShot catapult project). Board = sampler + Wi-Fi + page. The page runs calibration (prepare 3 / rest 5 /
  max 5 s, `config.CALIB_STEPS`) and all RMS / % maths; format `semgia-calib-2` (rest_rms / max_rms in counts).
- 2026-11-21 – Sensor now = **DFRobot Gravity Analog EMG SEN0240** (our PCB front end is not working): blue = signal →
  GPIO 34, red → 3V3/5V, black → GND. Analog output 0–3.0 V around 1.5 V (≈ 1860 counts), gain 1000, 20–500 Hz.
- 2026-11-19 BM – **Model options: logreg (default), lda, forest** on the 4 frozen features; `ThresholdModel` = floor;
  `Smoother` on top. Imbalance (rest 16 s : contract 8 s) via class weights / LDA equal priors, no resampling.
  Chosen from `docs/report/model_research.md`. List = `ML_KINDS` in `semgia/model.py`. Final pick on real train data.
- 2026-11-19 BM – **`TEST_PLACEMENTS` in `config.py` is the only test-set definition** (feeds `set` in metadata.csv,
  evaluate, train). Still empty → P1 picks the last placements once recorded.
- 2026-11-19 BM – **The course assignment is in `docs/course/`.** The Report 1 PDF is authoritative; slides/videos are
  background. Checklist + owners: `docs/course/requirements.md`. Build only what serves it.
- 2026-11-19 BM – **Every recording (train AND test sessions) stays in `data/raw/`**, marked `set = train|test` in
  `data/metadata.csv` (the PDF; the slides said "test only in Azure", PDF wins). Choose on train only, test once at the end.
- 2026-11-19 BM – No digital filter: analog front end = band-pass 20-447 Hz + 60 Hz notch; software only subtracts
  each window's mean (ESP32 offset ~2048).
- 2026-11-19 BM – Microcontroller = **ESP32**, 12-bit ADC (0..4095), `ADC_BITS = 12`.
- 2026-11-19 BM – Dashboard stays in the cloud (Azure). Colab = course documentation / project notebook (split still open).
- 2026-11-19 BM – Team skills in `.claude/skills/`: /gitup, /calib, /docit, /audit. Edit them via PR like code.
- 2026-11-19 BM – **No teammate approval for PRs.** Merge = `/gitup merge`: the AI squash-merges when CI is green,
  there are no conflicts and no foreign files/secrets; otherwise it stops and asks.
- 2026-11-19 BM – Git: own short-lived branch per task (`name/task`), PR to main within 1–2 days. Shared AI context
  = files on `main` (CLAUDE.md, MEMORY.md, docs/course/), so merge doc PRs first.
- 2026-11-20 – Web interface = ESP32 page (`http://192.168.4.1`, no HTTPS → browser can't write folders).
  It **downloads** `semgia_sample_*.json` / `semgia_calib_*.json`; `python scripts/import_web.py` (default: ~/Downloads)
  creates `data/raw/sample_NNN/` + `data/raw/calibration_EXX/` (format in data/CLAUDE.md). Sample numbers are given
  at import → import on ONE machine. The import replays each sample through the record.py pipeline
  (LivePredictor + SampleRecorder) → same signal.csv + predictions.csv; `--upload` sends it to Azure.
  `value` = raw 12-bit ADC count (0..4095), same as the serial path; import rejects anything else.
- 2026-11-18 – **Recording happens in our existing web interface** (Windows 11). It gets adapted for this protocol:
  "Collect sample" button → metadata popup → 24 s cues → folder `sample_NNN` with CSV + JSON.
  `scripts/record.py` (Python GUI) is only a backup / demo tool / reference implementation.
- 2026-11-18 – **Calibration once per patient + electrode placement**, using the web interface's existing sequence
  (rest + max contraction). All samples of that placement use it: 0 = rest level, 1 = max contraction.
  Replaces "each sample calibrates itself" (better for live use, no self-reference). **Not implemented yet** (see status).
- 2026-11-18 – Calibration removes only nuisance variation (electrode gain, skin contact). The AI still learns
  rest vs. contraction, effort and fatigue. `evaluate.py` will report calibrated vs. raw features for the report.
- 2026-11-18 – **1 sample = one continuous 24 s recording: rest 8 s / contract 8 s / rest 8 s** (professor's suggestion).
- 2026-11-18 – CSV = `t_s,value,label`. Label 0/1 is computed from the timer only (row / FS), never from the signal.
- 2026-11-18 – Transitions stay in the CSV. Training uses only "clean" windows ≥ 1.5 s (`TRIM_S`) away from a change
  → middle 5 s of each phase. Evaluation reports clean AND all windows (all = what the live app really sees).
- 2026-11-18 – Metadata has `placement_id` (E01, E02, … new number = electrodes re-applied),
  `effort` (light/medium/strong), `condition` (fresh/fatigued). Folders `data/raw/sample_NNN/`.
- 2026-11-18 – Evaluation = leave-one-**placement**-out (train placements only), balanced accuracy + accuracy.
- 2026-11-18 – Default model = logistic regression: 2 classes, 4 features, little data (~100 samples) → a simple model
  generalizes best to new placements, is explainable, trains in < 1 s. The final choice is made on real data with evaluate.py.
- 2026-11-03 – Python only, one package `semgia/`, thin scripts. No IoT Hub / Functions / Cosmos DB.
- 2026-11-03 – Azure = 1 Storage Account (Blob `signals`, Tables `samples` + `predictions`) + 1 App Service (Streamlit).
- 2026-11-03 – Uploads go directly to Storage every 2 s in a background thread. Local CSV is the source of truth.
- 2026-11-03 – FS = 1000 Hz, 200 ms windows, 100 ms step.
- 2026-11-03 – Pseudonyms P001 / OP01. Name list only on paper. EU Azure region. Repo stays private (also: course material in docs/course is students-only).

## Current status (2026-11-19)
- **Report 1 due Sat 2026-11-21 23:59.** Missing: README six parts, PROTOCOL.md, rationale/, ai-tools/, cue video,
  photos, tags. `DECISIONS.md` = draft (7, 8; Ben rewrites in own words; 9 by P3). `data/metadata.csv` +
  `QUALITY-REPORT.md` are generated by `scripts/export_metadata.py` / `scripts/check_quality.py` once real data exists.
- Repo scaffold merged: pipeline, tests, CI, docs, mock data, Python recording GUI, dashboard (local mode).
- **Calibration in code is still per-sample** (`processing.sample_dataset` uses the sample's first rest phase).
  Per-placement calibration: file format now known (`data/raw/calibration_EXX/`, data/CLAUDE.md). Change point: `sample_calibration`.
- Recording: web page (`firmware/semgia_emg/`, 2026-11-21): calibration + "Tomar muestra" + 24 s cues + downloads
  → `import_web.py`. Tested in a browser against a mock ESP32 + compiled; NOT yet run on the real boards.
- Hardware: real acquisition about to start. `firmware/emg_serial/emg_serial.ino` is written for an Arduino Uno (0..1023), not the ESP32.
- AI: fair-split evaluation (`evaluate.py`, `--final` = test once), smoothed score, fresh/fatigued split done. Runs on
  mock data only (scores ≈ 1.0, meaningless). Final model + TRIM_S/threshold check wait for real data (`first_look.py` ready).
- Azure: not set up yet. Upload + dashboard code tested offline / local mode only.

## Known problems / gotchas
- 2026-11-21 – SEN0240 saturates at 3.0 V ≈ 3720 counts, not 4095 → `check_signal` won't flag that clipping. Look at the
  plot. Its filters: 20–500 Hz, no 60 Hz notch stated (DFRobot does the notch in software) → filter decision above is for
  the PCB, P1/P2 to recheck with real data.
- 2026-11-20 – Demo fallback = `record.py --source file --file data/raw/sample_NNN/signal.csv`: replays a real
  sample, saves to `data/demo/` (gitignored), no upload. Dashboard `STEPS` must stay equal to `config.SAMPLE_STEPS`.
- 2026-11-20 – Web recording: keep the page in the foreground during a sample. If the browser falls > 8 s behind
  the ESP32 buffer the sample is aborted (nothing saved) → just repeat it. Page constants must match config.py
  (import_web.py rejects unknown dropdown values / other FS).
- 2026-11-19 BM – Electrode photos per session ARE required in Git now (`figures/`, no faces). Old rule "not in Git" is gone.
- 2026-11-18 – Record all samples on ONE machine (or `git pull` first): sample numbers are counted from the local
  `data/raw` folder, so two machines would both create e.g. `sample_012`.
- 2026-11-18 – Aborting during a sample leaves a partial folder (< 24 000 rows) → delete it by hand.
- 2026-11-19 BM – If the sensor only gives an envelope (e.g. MyoWare ENV pin), set `RAW_SIGNAL = False` in config.py:
  otherwise `features()` subtracts each window's mean and erases a steady contraction.
- 2026-11-03 – Streamlit on App Service needs WebSockets enabled and `--server.address 0.0.0.0 --server.port 8000`.
- 2026-11-03 – `LocalWriter` refuses to overwrite an existing sample folder (on purpose).

## Open questions
- Colab project notebook: one for the group, or one per member + one group? (ask the professor)
- Warning cue before the contraction (`warning_s`)? Currently 0 s.
- Professor's GitHub user, to add as collaborator. Member codes M01–M04: who is who?
- Raw output or envelope from the sensor? → decides RAW_SIGNAL.
- FS = 1000 Hz on the ESP32? FreeRTOS 1 ms task; the Serial Monitor prints `samples/s` every 10 s – confirm on hardware (P1).
- Which muscle? (default: biceps brachii right)
- The consent form MUST allow storing data on GitHub (Report 1 requires every recording in `data/raw/`). Check the wording.
- Is TRIM_S = 1.5 s right? Check on real train data with `scripts/first_look.py` (literature: onset ≈ 0.33 s after cue).
- Per-session values for metadata.csv (P1): electrode distance, skin preparation, sensor model, gain
  (`config.py`, now "TODO-P1").

## Glossary
- **sEMG** surface electromyography · **RMS** root mean square · **MAV** mean absolute value
- **WL** waveform length · **ZC** zero crossings · **MVC** maximum voluntary contraction
- **balanced accuracy** = mean of rest-accuracy and contraction-accuracy
- **Sample** = one 24 s recording (`sample_NNN`) · **Placement** = one electrode application (`E01`), many samples
- **Session** (course word) = one electrode placement = our `placement_id` · **Trial** = 1 cue-action-rest cycle = 1 sample for us
- **Calibration** = rest + max contraction once per placement → scales signals to 0 (rest) … 1 (max)
- **Clean window** = 200 ms window ≥ 1.5 s away from a label change
