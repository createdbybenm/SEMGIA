# Recording protocol

> Operator checklist. The method, the filter table and the members' agreement lines are in the root
> [PROTOCOL.md](../PROTOCOL.md). Patient = P002 (`config.PATIENT_ID`), muscle = right hamstrings.

**Goal:** ~100 samples = **10 electrode placements × 10 samples**, spread over ≥ 5 different days.
One sample = 24 s (rest 8 s → contract 8 s → rest 8 s). One placement ≈ 10 min.

## Before (5 min)
- [ ] Consent form signed (only once, kept on paper)
- [ ] Laptop **on battery, charger unplugged** (electrical safety)
- [ ] Always the **same recording laptop** (Windows 11, sample numbers are counted per laptop). `git pull` first.
- [ ] `.env` present (or record offline and run `upload_sample.py` later)
- [ ] Sensor connected, web page (`http://192.168.4.1`) shows the live graph and it moves when the muscle contracts
- [ ] Before **each** sample: strap tight, live signal quiet at rest. The hum grows during a placement (dry electrodes
      lose contact) and can push the signal to 0 → clipped, rejected sample (17 of 59 on 2026-11-21)

## Electrode placement (new placement ID each time electrodes go on)
1. Clean the skin with alcohol, let it dry. Shave if necessary.
2. 2 electrodes over the muscle belly along the fibre direction (~2 cm apart), reference electrode on bone (e.g. elbow).
3. Use the next placement ID: E01, E02, … Note the position in a few words.
4. **Take one photo of the electrodes** (no face, nothing identifying) → `figures/placement_EXX.jpg` (course requirement).

## Calibrate (once per placement)
Web page (Wi-Fi `SEMGIA-EMG`, `http://192.168.4.1`): fill in Sujeto `P001`, Operador `OP01`, Colocación `E01`,
then **1· Calibrar colocación** right after the electrodes are on. The machine guides: rest, then **maximum
contraction**. The page downloads `semgia_calib_E01_*.json` (needs the machine/station switched on).

## Record
In the web interface (Windows 11). Backup if it isn't ready: `python scripts/record.py --source serial --port COM3`.
1. Press **2· Tomar muestra** → check the form (effort/condition pre-filled from the plan below) → **Comenzar (24 s)**.
2. The subject follows the full-screen cue + beeps: green **REPOSO**, red **¡CONTRAIGA!**. Hold steadily for the whole 8 s.
   (Screen-record one sample once → this is our **cue video**, `cue/`.)
   Keep the page in the foreground. If it says "Muestra NO guardada", just repeat that sample.
3. After 24 s the page downloads `semgia_sample_E01_*.json`. Wait ~10 s (relax), then the next sample.
4. At the end, on the recording laptop: `python scripts/import_web.py` (add `--upload` if `.env` is set)
   → `data/raw/sample_NNN/` + `data/raw/calibration_E01/`.

**The 10 samples of one placement:**
| # | Effort | Condition | How |
|---|---|---|---|
| 1–3 | light | fresh | ~20 % of max |
| 4–6 | medium | fresh | ~50 % |
| 7–8 | strong | fresh | as strong as possible |
| 9–10 | medium | **fatigued** | first hold a strong contraction ~60 s (or do repetitions until tired), then record immediately |

Set **Effort** and **Condition** in the form correctly. This is how we analyse fatigue later.

## Rules during recording
- Don't touch the electrodes or cables during a sample. Arm rests on the table in the same position.
- Wrong reaction (contracted during rest, sneezed, cable pulled)? Let it finish, then **delete that folder**
  and record it again. Don't fix labels by hand.
- Closing the app during a sample leaves an incomplete folder → delete it.

## After
- [ ] Look at 1–2 samples in the dashboard (`streamlit run dashboard/app.py`): rest flat, contraction clearly bigger?
- [ ] Problems → one line in MEMORY.md
- [ ] Commit the samples on a branch `name/data-YYYY-MM-DD` → PR
- [ ] Remove the electrodes. The next placement gets a NEW ID
