# Team memory (shared, in Git)

One line per entry, newest first within a section, always dated (YYYY-MM-DD) + initials.
Add entries in the same PR as the change. Delete lines that are no longer true. Keep it < 150 lines.

## Decisions
- 2026-11-19 BM – **The course assignment is in `docs/course/`.** The Report 1 PDF is authoritative; slides/videos are
  background. Checklist + owners: `docs/course/requirements.md`. Build only what serves it.
- 2026-11-19 BM – **Every recording (train AND test sessions) stays in `data/raw/`**, marked `set = train|test` in
  `data/metadata.csv` (the PDF; the slides said "test only in Azure", PDF wins). Choose on train only, test once at the end.
- 2026-11-19 BM – The analog front end has a **60 Hz notch** (Mexico). Software `NOTCH_HZ = 50` is wrong → fix (P2).
- 2026-11-19 BM – Dashboard stays in the cloud (Azure). Colab = course documentation / project notebook (split still open).
- 2026-11-19 BM – Git: own short-lived branch per task (`name/task`), PR to main within 1–2 days. Shared AI context
  = files on `main` (CLAUDE.md, MEMORY.md, docs/course/), so merge doc PRs first.
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
- 2026-11-18 – Evaluation = leave-one-**placement**-out, balanced accuracy. Models compared: threshold, logreg, forest.
- 2026-11-18 – Default model = logistic regression: 2 classes, 4 features, little data (~100 samples) → a simple model
  generalizes best to new placements, is explainable, trains in < 1 s. The final choice is made on real data with evaluate.py.
- 2026-11-03 – Python only, one package `semgia/`, thin scripts. No IoT Hub / Functions / Cosmos DB.
- 2026-11-03 – Azure = 1 Storage Account (Blob `signals`, Tables `samples` + `predictions`) + 1 App Service (Streamlit).
- 2026-11-03 – Uploads go directly to Storage every 2 s in a background thread. Local CSV is the source of truth.
- 2026-11-03 – FS = 1000 Hz, 200 ms windows, 100 ms step, bandpass 20–450 Hz.
- 2026-11-03 – Pseudonyms P001 / OP01. Name list only on paper. EU Azure region. Repo stays private (also: course material in docs/course is students-only).

## Current status (2026-11-19)
- **Report 1 due Sat 2026-11-21 23:59.** None of the required root files exist yet (README six parts, PROTOCOL.md,
  DECISIONS.md, QUALITY-REPORT.md, data/metadata.csv, rationale/, ai-tools/, cue video, photos, tags). See tasks.md.
- Repo scaffold merged: pipeline, tests, CI, docs, mock data, Python recording GUI, dashboard (local mode).
- **Calibration in code is still per-sample** (`processing.sample_dataset` uses the sample's first rest phase).
  Next step: switch to per-placement calibration as soon as the web interface's calibration file format is known.
- Web interface: codebase will be shared → then adapt it (sample button, markers, folder output).
- Hardware: real acquisition about to start. Firmware sketch untested on hardware.
- AI: runs on mock data only (scores ≈ 1.0 on synthetic data – meaningless until real data exists).
- Azure: not set up yet. Upload + dashboard code tested offline / local mode only.

## Known problems / gotchas
- 2026-11-19 BM – Electrode photos per session ARE required in Git now (`figures/`, no faces). Old rule "not in Git" is gone.
- 2026-11-18 – Record all samples on ONE machine (or `git pull` first): sample numbers are counted from the local
  `data/raw` folder, so two machines would both create e.g. `sample_012`.
- 2026-11-18 – Aborting during a sample leaves a partial folder (< 24 000 rows) → delete it by hand.
- 2026-11-03 – If the sensor only gives an envelope (e.g. MyoWare ENV pin), set `RAW_SIGNAL = False` in config.py.
- 2026-11-03 – Streamlit on App Service needs WebSockets enabled and `--server.address 0.0.0.0 --server.port 8000`.
- 2026-11-03 – `LocalWriter` refuses to overwrite an existing sample folder (on purpose).

## Open questions
- Colab project notebook: one for the group, or one per member + one group? (ask the professor)
- Movement vs. rest balance (PDF: "about the same amount"): ours is 8 s vs. 16 s → class weights or protocol change?
- Warning cue before the contraction (`warning_s`)? Currently 0 s.
- Professor's GitHub user, to add as collaborator. Member codes M01–M04: who is who?
- Web interface: where is the repo, what does it save today (format of calibration + recordings), how are markers set?
- Raw output or envelope from the sensor? Which microcontroller? → decides FS and RAW_SIGNAL.
- Which muscle? (default: biceps brachii right)
- The consent form MUST allow storing data on GitHub (Report 1 requires every recording in `data/raw/`). Check the wording.
- Is TRIM_S = 1.5 s right? Check on real data: plot a few samples and look where the contraction really starts/stops.

## Glossary
- **sEMG** surface electromyography · **RMS** root mean square · **MAV** mean absolute value
- **WL** waveform length · **ZC** zero crossings · **MVC** maximum voluntary contraction
- **balanced accuracy** = mean of rest-accuracy and contraction-accuracy
- **Sample** = one 24 s recording (`sample_NNN`) · **Placement** = one electrode application (`E01`), many samples
- **Session** (course word) = one electrode placement = our `placement_id` · **Trial** = 1 cue-action-rest cycle = 1 sample for us
- **Calibration** = rest + max contraction once per placement → scales signals to 0 (rest) … 1 (max)
- **Clean window** = 200 ms window ≥ 1.5 s away from a label change
