# What the course requires (and where it lives in this repo)

Source of truth: [report1_assignment.md](report1_assignment.md) (transcript of the PDF). The slides
([slides.md](slides.md)) are background. **If they disagree, the PDF wins.** Unclear → ask the team, don't invent.

**Goal:** one person (P001), one movement. Two classes: movement / rest. **> 75 % right on sessions the model never saw**
(new electrodes). At the end the model runs, and every measurement is saved with its metadata in a cloud service (Azure).

## Deadlines
| Date | What |
|---|---|
| **Sat 2026-11-21 23:59** | **Report 1** (not graded, but required): one repo link per group, professor = collaborator |
| **2026-11-24** final class | Final delivery: live demo, test on 4 new placements, exam (from slides, see below) |

## Report 1 checklist → our repo
Status as of 2026-11-21. The files must sit at the **repo root**, with exactly these names.

| # | Required | Our status / source in repo | Owner |
|---|---|---|---|
| 1 | `README.md`: six parts (see below) + team table: member code, GitHub user, role, AI tool | done (team table: M03/M04 rows to confirm) | P4 |
| 2 | `PROTOCOL.md`: method, **type, order and limits of every filter + source** (ours: analog band-pass 20–500 Hz + digital 60 Hz notch with harmonics, see architecture.md), 1 line per member "I read the method and I agree" (own commit each) | done at root; agreement lines: M02 on main, M01 in PR #12, M03/M04 missing | P1 |
| 3 | `data/raw/`: **every** recording, untouched (train **and** test sessions) | done: 59 recordings, E01–E06 (2026-11-21) | P1 |
| 4 | `data/metadata.csv`: one row per recording, columns below | done (distance + skin preparation = "not recorded") | P2 |
| 5 | `QUALITY-REPORT.md`: one row per recording + reason for each rejection | done: 26 of 59 rejected | P2 |
| 6 | `DECISIONS.md`: parts 7 Features, 8 Model, 9 Route (chose / reason in own words / not understood yet) | done (7, 8, 9) | P2 (7, 8), P3 (9) |
| 7 | `rationale/Mxx.md`: ~100 words, own words, one group choice you support or doubt + why + 1 source | M02 done; M01, M03, M04 missing | **each member** |
| 8 | `ai-tools/Mxx.png`: screenshot of your AI tool open on this project with one question | M02 done, M01 in PR #12; M03, M04 missing | **each member** |
| 9 | cue video (e.g. `cue/cue-video.mp4`, screen recording of our REST/CONTRACT cues) | missing | P1 / P4 |
| 10 | one electrode photo **per session**, no faces (e.g. `figures/placement_S01.jpg`) | missing (old rule "photos not in Git" is obsolete) | P1 |
| 11 | tags `v0-first` and `v1-report`; ≥ 1 commit per member; professor added as collaborator | tags done; professor invited (pending); commits: M01, M02, M03 yes, M04 not yet | P4 |

### The six README parts (write numbers, not adjectives; end each with "Evidence: <files/columns>")
1 Data acquisition (recordings, trials, sessions, persons, electrodes, distance, muscle, Fs) · 2 Task (movement, 2 classes,
posture) · 3 Trial and cue timing (seconds of each phase, trials per recording, cue video) · 4 Sessions (how many, which
days, new electrodes each) · 5 Cleaning (filters + rejection rule + how many rejected) · 6 Fair split (which sessions
train, which test, none in both, limits of the claim). If the sensor gives a smoothed/envelope signal, say so.

### Required `data/metadata.csv` columns
`session, date, rest_s, warning_s, move_s, between_s, electrode_type, electrode_distance_cm, skin_preparation,
sensor_model, gain, fs_hz, adc_bits, set` (`set` = train | test). Add `file_name` + our own fields too (see
[example_repo.md](example_repo.md)). Our `metadata.json` lacks `electrode_distance_cm, skin_preparation, sensor_model,
gain, adc_bits, set` → the export script fills them from per-session constants, so the frozen `METADATA_FIELDS` stay
unchanged unless the team agrees otherwise.

## How the course words map onto ours
| Course | Ours |
|---|---|
| session (one electrode placement) | `placement_id` E01, E02, … (write as S01, S02 in course files, or keep E01 and define it in the README) |
| recording | one sample `sample_NNN` (24 s) |
| trial (cue, action, rest) | 1 per recording: rest 8 / contract 8 / rest 8 → `rest_s=8, warning_s=0, move_s=8, between_s=8` (to confirm) |
| participant P01 | subject `P001` |
| member code | M01–M04 (assign in README team table) |

## Rules from the PDF that change how we work
- **Fair split:** fixed train sessions vs. test sessions, no session in both, no windows of one recording on both sides.
  **Choose features and model with the training sessions only** (our leave-one-placement-out runs inside train).
  **Open the test sessions once, at the end.** Anything else = leakage.
- **Keep about the same amount of movement and rest.** Ours: 8 s move vs. 16 s rest per sample (clean: 5 s vs. 10 s).
  → decided: class weights in training, no resampling (MEMORY.md 2026-11-19, DECISIONS.md part 8).
- **Cleaning rule written before any score:** reject a recording/trial if a sample sits at the ADC limit (0 or
  2^bits − 1), if samples are missing, or if its length is off by > 2 % from 24 000 (course check, slides 15).
- **Filters:** analog band-pass 20-500 Hz (SEN0240 board) + digital 60 Hz notch with harmonics (`processing.Filter`,
  added 2026-11-21 because the data was mostly hum) + offset removal per window. Write all of them + source in PROTOCOL.md.
  Band-pass upper limit must be < Fs/2 (course band 20–450 Hz, source: course / McManus 2020). Ours: 447 Hz < 500 Hz
  if FS = 1000 Hz (FS on the ESP32 still to confirm).
- **Report the score next to its floors:** chance (≈ 50 % with balanced classes) and a single threshold on one feature
  (our `ThresholdModel`), plus a confusion matrix. Course metric = accuracy; we also give balanced accuracy.
- **Don't copy the example.** Own movement, own seconds, own words.
- **Privacy:** codes, never names; no faces in photos/video; private repo; health data = sensitive (Mexico LFPDPPP).

## Final delivery 2026-11-24 (from the slides: background, check with the professor)
| Part | Points | What |
|---|---|---|
| Training data | 10 | ≥ 100 recordings of movement + rest, new electrodes every 10, metadata, in GitHub |
| Test + accuracy | 10 | final class: new electrodes 4 times, data to the cloud (Azure), ≥ 75 % · ours so far: logreg 0.887 on test session E06 (2026-11-24, `docs/report/results_test.md`) |
| Demo | 10 | live; if hardware fails, the method is graded (→ our `--source file` fallback) |
| Code design | 15 | small functions, a test each, no secrets; **every member explains the code** |
| Project notebook (Colab) | 15 | rules, method, results, who did what, what each member learned (5 pts individual) |
| Exam | 40 | on paper, question bank |
Also: norms (research vs. medical product, COFEPRIS), consent signed before the first recording, signed recording rules.

## Open questions (ask the professor or decide as a team)
- Colab: one project notebook for the group, or one per member + one group? The slides say the dashboard runs in Colab; we
  keep the dashboard in Azure and use Colab for documentation.
- Slides: "test data only in Azure", PDF: every recording in `data/raw/` → we follow the PDF for Report 1.
- Do we need a warning cue (`warning_s`)? Current protocol has none (0 s).
