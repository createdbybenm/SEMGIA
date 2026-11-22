# Protocol

One person (patient P002), one muscle (right hamstrings), one movement (contract and hold). Step-by-step operator
checklist: [docs/protocol.md](docs/protocol.md). Codes only: subject P002, operator OP01, sessions E01, E02, …

## Method
1. **Setup.** DFRobot Gravity Analog EMG sensor SEN0240 (OYMotion), dry electrodes built into the board, strapped
   over the belly of the right hamstrings. Analog output → ESP32 GPIO 34, 12-bit ADC (0..4095), 1000 samples/s.
   The ESP32 serves the recording web page over Wi-Fi; the browser downloads one JSON file per recording.
   Laptop on battery while recording.
2. **New session = new electrode placement.** Electrodes off and on again, next session code (E01, E02, …).
3. **Calibration, once per session** (13 s, guided by the page with beeps): prepare 3 s, relax 5 s, maximum
   contraction 5 s. Rest and maximum RMS are saved per session (`semgia_calib_EXX_*.json`).
4. **Recording = one trial of 24 s**, with a full-screen cue and a beep at every change:
   rest 8 s (green REPOSO) → contraction 8 s (red ¡CONTRAIGA!) → rest 8 s. No warning cue.
   The operator fills in effort and condition before each recording.
5. **Plan per session (10 recordings):** 3 light, 3 medium, 2 strong (fresh), then 2 medium after fatiguing the muscle
   (hold a strong contraction until tired, record immediately). About 10 s of rest between recordings.
6. **Labels** come only from the timer: row 0–7999 = rest (0), 8000–15999 = contraction (1), 16000–23999 = rest (0).
   Nothing is cut out of the file. Training skips windows closer than 1.5 s to a cue change.
7. **Import:** `python scripts/import_web.py` turns the downloads into `data/raw/sample_NNN/` (`signal.csv` with
   `t_s,value,label`, `metadata.json`) in recording order. Values are stored untouched.
8. **Quality check** (rule fixed before any model score, `QUALITY-REPORT.md`): reject a recording if a value sits at
   the ADC limit (0 or 4095), if a value or row is missing, if the length is off by more than 2 %, or if it is not
   from the patient P002.

## Filters (in signal order)
| # | Filter | Type and order | Limits | Source |
|---|---|---|---|---|
| 1 | Band-pass + amplifier on the sensor board | analog; order not stated by the manufacturer; gain 1000 | 20–500 Hz. Output 0–3.0 V around 1.5 V; the upper edge equals Fs/2 (500 Hz), so there is no extra margin against aliasing | DFRobot wiki, *Gravity: Analog EMG Sensor by OYMotion (SKU SEN0240)*, https://wiki.dfrobot.com/Analog_EMG_Sensor_by_OYMotion_SKU_SEN0240 |
| 2 | 60 Hz notch | digital IIR notch, 2nd order per notch, at 60 Hz and every harmonic below Fs/2 (60, 120, … 480 Hz), cascaded, causal | Q = 30 → −3 dB width 2 Hz per notch; the SEN0240 has no analog notch, so this removes mains interference (Mexico, 60 Hz) | SciPy `scipy.signal.iirnotch` documentation; `semgia/processing.py` (`Filter`, constants `NOTCH_HZ`, `NOTCH_Q` in `semgia/config.py`) |
| 3 | Offset removal | subtract the mean of each 200 ms window (before the features) | removes the sensor offset (≈ 1650 counts at rest) and drifts slower than one window | `semgia/processing.py` (`features`) |

The same three steps run live and offline (one code path), so the model sees the same signal in both cases.
`data/raw/` keeps the unfiltered ADC values; filters 2 and 3 are applied in code.

## Agreement (one line per member, each from their own account)
- M01 (Silver0-sys): I read the method and I agree.
- M02 (createdbybenm): I read the method and I agree.
- M03 (CarlosOVa): I read the method and I agree.
- M04 (Ximenaabreugg): I read the method and I agree.
