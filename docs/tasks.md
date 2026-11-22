# Who does what (until 2026-11-24)

Four roles. Each person owns **their folders**, so nobody edits the same file at the same time.
Every task = a GitHub issue → a branch `yourname/task` → a PR → CI green + no conflicts → squash merge (`/gitup merge`).
Start every Claude session with: *"Read MEMORY.md and the CLAUDE.md of <your folder>, then do <task>."*

---

## Report 1: due Sat 2026-11-21 23:59 (checklist: `docs/course/requirements.md`)
Each item goes on its own branch + PR. Don't copy the professor's example (it gets returned).

| Who | Task |
|---|---|
| **Everyone** | `rationale/Mxx.md` (~100 words, own words, 1 source) · `ai-tools/Mxx.png` (screenshot of your AI tool on this repo + 1 question) · your "I read the method and I agree" line in PROTOCOL.md · ≥ 1 commit from **your own** account · fill your row of the team table |
| P1 Hardware | record sessions (mark some as test, e.g. the last 2) · 1 electrode photo per session → `figures/` · cue video → `cue/` · root `PROTOCOL.md` from `docs/protocol.md` + filter table (analog 60 Hz notch: type, order, limits, source) |
| P2 AI (Ben) | no digital filter (analog band-pass 20-447 Hz + 60 Hz notch); software only removes the offset per window - done · `scripts/export_metadata.py` → `data/metadata.csv` (14 required columns, `set`) · `scripts/check_quality.py` → `QUALITY-REPORT.md` (clipping, missing, length ±2 %) · fair split in `evaluate.py` (choose on train, test once; floors + confusion matrix) · `DECISIONS.md` parts 7 + 8 |
| P3 Azure | `DECISIONS.md` part 9 (route: model on laptop, record to Azure) + screenshot of one saved record with metadata · privacy/consent wording (LFPDPPP, GitHub storage) |
| P4 Interface | root `README.md`: six parts with numbers + "Evidence:" lines + team table (member code, GitHub user, role, AI tool) · add the professor as collaborator · tag `v0-first` now, `v1-report` at the end |

## Person 1 – Hardware & recordings
**Owns:** `firmware/`, `semgia/sources.py`, `docs/protocol.md`, `data/raw/`

1. **Get the signal into the PC.** Flash `firmware/emg_serial/emg_serial.ino` (Arduino IDE → Upload).
   Check in the Serial Plotter, then run `python scripts/record.py --source serial --port COM3`.
   *Done when:* the live plot moves when the muscle contracts.
2. **Raw or envelope?** Look at the plot: oscillating around a middle value = raw (keep `RAW_SIGNAL = True`);
   smooth hill during contraction = envelope (set `RAW_SIGNAL = False` in `semgia/config.py`). Write it in MEMORY.md.
3. **Consent form** (see `docs/privacy.md`), muscle choice → MEMORY.md.
4. **Run the recordings** with `docs/protocol.md`: 10 placements × 10 samples, ≥ 5 days. Everyone helps as operator/subject.
5. Commit samples via PR `yourname/data-YYYY-MM-DD`. Log problems in MEMORY.md.

## Person 2 – AI (signal processing & models)
**Owns:** `semgia/processing.py`, `semgia/model.py`, `semgia/evaluation.py`, `semgia/report.py`, `scripts/train.py`,
`scripts/evaluate.py`, `scripts/first_look.py`, `scripts/export_metadata.py`, `scripts/check_quality.py`, `notebooks/`

1. ✅ **Now (no data needed):** `python scripts/make_mock_samples.py && python scripts/evaluate.py --data data/synthetic`.
   Read `processing.sample_dataset`. Understand clean windows + baseline.
2. **Per-placement calibration** (agreed, see MEMORY.md): once the web interface's calibration file format is known,
   change `sample_dataset` to scale with the placement's calibration (0 = rest, 1 = max contraction) instead of
   the sample's own rest phase. Add a "no calibration" column to `evaluate.py` (calibrated vs. raw).
3. **First real samples:** `python scripts/first_look.py --data data/raw` (ready): plot signal + label of 3 samples.
   Where does the contraction really start/stop? → is `TRIM_S = 1.5` right? Are `THRESHOLD_ON/OFF` (3×/2× rest) right?
4. **After ≥ 3 placements:** `python scripts/evaluate.py --out docs/report/results.md`.
5. ✅ **Fatigue check:** `evaluate.py` already scores `fresh` vs. `fatigued` separately; read it on real data.
6. **Final model:** `python scripts/train.py` → commit `models/model.joblib`. Decision + numbers → MEMORY.md.
   Only change the model if leave-one-placement-out gets better.

## Person 3 – Azure & data privacy
**Owns:** `semgia/storage.py`, `docs/azure_setup.md`, `docs/privacy.md`, `dashboard/` deployment

1. **Set up Azure** exactly as in `docs/azure_setup.md` (resource group, Storage Account, budget alert, access for all).
2. **Give everyone the connection string** privately → each person puts it in their own `.env`.
3. **Test the upload:** `python scripts/record.py --source mock` → record a sample → check in the Azure portal
   (Storage browser): `signals/sample_NNN/` and tables `samples` and `predictions`.
4. **Deploy the dashboard** to App Service (`docs/azure_setup.md` step 3). Send the URL to the team.
5. **Offline fallback:** record with Wi-Fi off, then `python scripts/upload_sample.py data/raw/sample_NNN`.
6. Test deleting one sample everywhere (`docs/privacy.md`). Write the privacy section of the report.

## Person 4 – Web interface (recording) & dashboard
**Owns:** our web interface (`firmware/HamShot_EMG/pagina.h`), `scripts/record.py` (backup), `semgia/recorder.py`,
`dashboard/app.py`, `README.md`, CI

1. **Now:** `python scripts/record.py --source mock` → click through a sample. This is the reference for the flow.
2. **Adapt the web interface** (Windows 11) to the same flow: calibration once per placement (existing sequence:
   rest + max contraction) → "Collect sample" → metadata popup (fields = `METADATA_FIELDS` in `semgia/storage.py`,
   dropdowns from `semgia/config.py`) → 24 s cues REST 8 / CONTRACT 8 / REST 8 → folder `data/raw/sample_NNN/` with
   `signal.csv` (`t_s,value,label`, label from the timer) + `metadata.json`. Big readable banner, sample counter.
   Test: `python scripts/train.py` must read the folders it writes. Write the calibration file format into
   `data/CLAUDE.md` + MEMORY.md.
3. **Dashboard** (`streamlit run dashboard/app.py`): add the label (0/1) as a second line under the signal,
   a list of samples per placement, contraction % per sample.
4. **Demo mode:** `python scripts/record.py --source file --file data/raw/sample_005/signal.csv` must work
   as a fallback if the sensor fails during the presentation.
5. README screenshots, keep CI green.

---

## Timeline
| When | Milestone |
|---|---|
| this week | sensor → signal on the PC · web interface writes the sample folders · Azure set up · per-placement calibration in code |
| next days | all 10 placements recorded · evaluate.py results (calibrated vs. raw) · dashboard on Azure |
| **2026-11-21 23:59** | **Report 1 handed in** (tag `v1-report`), then feature freeze: only bug fixes, notebook, rehearsal |
| 2026-11-24 | final class: 4 new placements → Azure, ≥ 75 %, live demo (or file fallback), Colab notebook, exam, tag `v1.0` |
