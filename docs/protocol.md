# Recording protocol

> For Report 1 this becomes the root `PROTOCOL.md` (owner P1): add the type, order, limits and source of every filter
> (analog 60 Hz notch + software filters) and one "I read the method and I agree" line per member (own commit each).

**Goal:** ~100 samples = **10 electrode placements × 10 samples**, spread over ≥ 5 different days.
One sample = 24 s (rest 8 s → contract 8 s → rest 8 s). One placement ≈ 10 min.

## Before (5 min)
- [ ] Consent form signed (only once, kept on paper)
- [ ] Laptop **on battery, charger unplugged** (electrical safety)
- [ ] Always the **same recording laptop** (Windows 11, sample numbers are counted per laptop). `git pull` first.
- [ ] `.env` present (or record offline and run `upload_sample.py` later)
- [ ] Sensor connected, Arduino Serial Plotter shows a signal, then close the Serial Plotter (it blocks the port)

## Electrode placement (new placement ID each time electrodes go on)
1. Clean the skin with alcohol, let it dry. Shave if necessary.
2. 2 electrodes over the muscle belly along the fibre direction (~2 cm apart), reference electrode on bone (e.g. elbow).
3. Use the next placement ID: E01, E02, … Note the position in a few words.
4. **Take one photo of the electrodes** (no face, nothing identifying) → `figures/placement_EXX.jpg` (course requirement).

## Calibrate (once per placement)
Run the web interface's calibration sequence right after the electrodes are on: rest, then **maximum contraction**.
Save it under the placement ID (exact file format: to be defined when the web interface is adapted).

## Record
In the web interface (Windows 11). Backup if it isn't ready: `python scripts/record.py --source serial --port COM3`.
1. Press **Collect sample** → fill in the form (pre-filled from the last sample) → **Start recording (24 s)**.
2. The subject follows the banner: green **REST**, red **CONTRACT**. (Screen-record one sample once → this is our **cue video**, `cue/`.) Hold the contraction steadily for the whole 8 s.
3. After 24 s it shows "Saved sample_NNN". Wait ~10 s (relax), then the next sample.

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
