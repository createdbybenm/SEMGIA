# Team memory (shared, in Git)

One line per entry, newest first within a section, always dated (YYYY-MM-DD) + initials.
Add entries in the same PR as the change. Delete lines that are no longer true. Keep it < 150 lines.

## Decisions
- 2026-11-24 BM – **Per-placement calibration is NOT built for the final.** Final class is today; the calibration files
  are `semgia-calib-2` (unmerged PR #8) and `import_web.py` only reads `semgia-calib-1`. The final test uses the
  per-sample rest baseline. Building it now would touch both baseline paths (`processing.sample_calibration` and
  the live one in `recorder.SampleRecorder.push`) and need its own train-only comparison before any test.
- 2026-11-24 BM – Domain words live in `GLOSSARY.md`. Code/hardware gotchas live in the CLAUDE.md of their folder,
  not here. This file = decisions, status, open questions.
- 2026-11-21 CO – Consent form written: `docs/consent_form.docx` (print, fill blanks by hand, sign on paper; covers GitHub + Azure EU storage; one per person: P001 for E01, P002 for E02–E06). Signed copies stay on paper.
- 2026-11-21 CO/BM – Sensor gives the raw signal (not an envelope) → `RAW_SIGNAL = True`. FS = 1000 Hz confirmed (hum
  peak exactly at 60.0 Hz). Muscle = right hamstrings.
- 2026-11-21 BM – PROTOCOL.md lists the digital 60 Hz notch as filter 2 (course: type, order, limits of EVERY filter).
  `data/raw/` stays unfiltered; notch + window-mean removal run in code (`Filter`, `features`).
- 2026-11-21 BM – Model still open: on train LOPO logreg and LDA tie (0.90 clean / 0.85 all), forest 0.88 / 0.83.
  Pick the best on train only, then `evaluate.py --final` once on E06.
- 2026-11-21 BM – `notebooks/` folder removed: no notebooks in the repo for now. The course's Colab project notebook
  (final delivery) is still open, see Open questions.
- 2026-11-21 BM – **Digital 60 Hz notch + harmonics in `processing.Filter`** (`NOTCH_HZ`, `NOTCH_Q`; causal, with state).
  The real data is 50–99 % mains hum at rest, the SEN0240 has no notch. Replaces "no digital filter" (2026-11-19).
- 2026-11-21 BM – **Patient = P002** (`config.PATIENT_ID`). Round 1 (E01) was another person (P001): imported (every
  recording stays) but rejected in QUALITY-REPORT ("other subject"). The final test on 11-24 must be on P002 too.
- 2026-11-21 BM – Muscle = **hamstrings** (added to `MUSCLES`; the web form had no such choice → 'other' was typed).
  Wrong form fields are fixed at import with `import_web.py --set KEY=VALUE`, never by editing data/raw.
- 2026-11-21 – **ESP32 firmware + web page are in this repo: `firmware/HamShot_EMG/`** (was a local "separate repo").
  Only the EMG board; the catapult station sketch is NOT in the repo (not part of the assignment).
- 2026-11-21 – Sensor now = **DFRobot Gravity Analog EMG SEN0240** (our PCB front end is not working): blue = signal →
  GPIO 34, red → 3V3/5V, black → GND. Wiring + output levels: `firmware/CLAUDE.md`.
- 2026-11-19 BM – **Model options: logreg (default), lda, forest** on the 4 frozen features; `ThresholdModel` = floor;
  `Smoother` on top. Imbalance (rest 16 s : contract 8 s) via class weights / LDA equal priors, no resampling.
  Chosen from `docs/report/model_research.md`. List = `ML_KINDS` in `semgia/model.py`. Final pick on real train data.
- 2026-11-19 BM – **`TEST_PLACEMENTS` in `config.py` is the only test-set definition** (feeds `set` in metadata.csv,
  evaluate, train). Set to `["E06"]` on 2026-11-21 (last placement).
- 2026-11-19 BM – **The course assignment is in `docs/course/`.** The Report 1 PDF is authoritative; slides/videos are
  background. Checklist + owners: `docs/course/requirements.md`. Build only what serves it.
- 2026-11-19 BM – **Every recording (train AND test sessions) stays in `data/raw/`**, marked `set = train|test` in
  `data/metadata.csv` (the PDF; the slides said "test only in Azure", PDF wins). Choose on train only, test once at the end.
- 2026-11-19 BM – Microcontroller = **ESP32**, 12-bit ADC (0..4095), `ADC_BITS = 12`.
- 2026-11-19 BM – Dashboard stays in the cloud (Azure). Colab = course documentation / project notebook (split still open).
- 2026-11-19 BM – Team skills in `.claude/skills/`: /gitup, /calib, /docit, /audit. Edit them via PR like code.
- 2026-11-19 BM – **No teammate approval for PRs.** Merge = `/gitup merge`: the AI squash-merges when CI is green,
  there are no conflicts and no foreign files/secrets; otherwise it stops and asks.
- 2026-11-19 BM – Git: own short-lived branch per task (`name/task`), PR to main within 1–2 days. Shared AI context
  = files on `main` (CLAUDE.md, MEMORY.md, docs/course/), so merge doc PRs first.
- 2026-11-20 – Web interface = HamShot ESP32 page (`http://192.168.4.1`, no HTTPS → browser can't write folders).
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
  Replaces "each sample calibrates itself" (better for live use, no self-reference). **Not built** (see 2026-11-24).
- 2026-11-18 – Calibration removes only nuisance variation (electrode gain, skin contact). The AI still learns
  rest vs. contraction, effort and fatigue.
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

## Current status (2026-11-24, final class)
- 2026-11-20 CO – **Azure is set up** (subscription "Azure for Students", not "ITESM - LabVirtual"): `rg-semgia`,
  Storage `semgiadatabossvl` in **belgiumcentral** (westeurope is blocked by the student policy; belgiumcentral is the
  only allowed EU region). Tested: mock sample uploads live, offline sample uploads later, `scripts/delete_sample.py`.
  Connection string: ask CO privately, never in Git.
- 2026-11-21 CO – **Dashboard online (free F1 plan)**: https://semgia-dashboard-bossvl.azurewebsites.net
  (first load ~1 min, it sleeps). Budget `semgia-budget` 10/month, alert at 80%. No paid plans (team choice).
- **Report 1:** on main: README (six parts + team table, M01–M04 confirmed), PROTOCOL.md (4 agreement lines),
  DECISIONS.md 7–9, data/raw + metadata.csv + QUALITY-REPORT, rationale/ + ai-tools/ M01–M04, consent form,
  tags `v0-first` (56d499c) + `v1-report` (still on d68e075). **Still missing:** cue video (`cue/`), electrode photo
  per session (`figures/`). Files added after d68e075 → move the tag: `git tag -f v1-report && git push -f origin v1-report`.
- 2026-11-21 BM – metadata.csv: `electrode_distance_cm` + `skin_preparation` = "not recorded" (SEN0240 built-in dry
  electrodes, nothing written down). Posture of the person was not recorded either.
- **Real data in Git (2026-11-21):** `data/raw/sample_001–059`, E01–E06 (E01 = P001, other subject). `data/metadata.csv`
  + `QUALITY-REPORT.md` generated: 26 rejected (9 other subject, 17 clipped at 0) → 23 train (E02–E05) + 10 test (E06).
  Import fixes (`--set`): muscle=hamstrings for all; effort=strong for E02 (sample_010–019, user: round 2 was all
  strong); condition fresh for sample_019 (typed "fewah"). effort/condition elsewhere = as typed, partly unreliable.
  Calibration files (`semgia-calib-2`) not imported yet → after PR #8. E01 false starts 223604Z/223632Z = drop.
- AI on real train data (LOPO E02–E05, `docs/report/results_train.md`): logreg 0.90 / 0.85, LDA 0.90 / 0.85,
  forest 0.88 / 0.83 (clean / all windows); threshold floor 0.80 / 0.78, chance 0.67. Test (E06) not opened yet.
  Not run yet: `first_look.py` (TRIM_S / threshold check), `train.py` (no `models/model.joblib`).
- **Calibration in code is per-sample** (first rest phase), offline in `processing.sample_calibration` and live in
  `recorder.SampleRecorder.push`. Per-placement calibration not built (Decisions 2026-11-24).
- Recording: the 2026-11-21 data came from the standalone page of PR #8 (`firmware/semgia_emg/`, `semgia-calib-2`,
  still open). `firmware/HamShot_EMG/` on main is the older version. SEN0240 on the ESP32, real boards work.

## Known problems / gotchas
Gotchas live next to their code: sensor + web page → `firmware/CLAUDE.md`, recording → `docs/protocol.md`,
data folders → `data/CLAUDE.md`, pipeline → `semgia/CLAUDE.md`, replay demo → `scripts/CLAUDE.md`, Azure → `dashboard/CLAUDE.md`.
- 2026-11-21 BM – Real data: the hum grows during each placement (dry electrodes lose contact) and pushes the signal
  to 0 → 17 of 59 samples clipped (see `docs/protocol.md` → before each sample).

## Open questions
- Colab project notebook: one for the group, or one per member + one group? (ask the professor)
- Warning cue before the contraction (`warning_s`)? Currently 0 s.
- Posture of the person during recording (README part 2) – not written down yet (P1).
- Is TRIM_S = 1.5 s right? Check on real train data with `scripts/first_look.py` (literature: onset ≈ 0.33 s after cue).
