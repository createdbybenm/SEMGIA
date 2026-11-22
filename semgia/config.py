"""All tunable constants in one place. Change values here, not in the modules."""

from pathlib import Path

# --- Signal ---
FS = 1000                 # sampling rate in Hz (must match firmware)
RAW_SIGNAL = True         # False if the sensor outputs an envelope (e.g. MyoWare ENV pin)
ADC_MID = 2048            # ESP32 mid-scale: where a raw signal sits at rest (only used by MockSource)
# Digital notch (processing.Filter): real data 2026-11-21 was 50-99 % mains hum at rest (60 Hz + harmonics),
# the sensor has no working notch. Software also subtracts each window's mean in processing.features.
NOTCH_HZ = 60.0           # Mexico mains; every multiple below FS/2 is notched too (60, 120, ... 480 Hz)
NOTCH_Q = 30.0            # quality factor: -3 dB width = NOTCH_HZ / NOTCH_Q = 2 Hz per notch

# --- Windowing ---
WINDOW_S = 0.200          # 200 ms windows
STEP_S = 0.100            # one prediction every 100 ms
WINDOW = int(WINDOW_S * FS)
STEP = int(STEP_S * FS)

# --- Sample protocol: one sample = one continuous 24 s recording ---
REST, CONTRACT = 0, 1
SAMPLE_STEPS = [(REST, 8), (CONTRACT, 8), (REST, 8)]   # (label, seconds)
WARNING_S = 0             # no warning cue before the contraction (open question)
SAMPLES_PER_PLACEMENT = 10  # plan per placement (= web page N_PLAN): cue screen shows "sample 4 of 10"
TRIM_S = 1.5              # windows closer than this to a label change / the start / the end are not "clean"
                          # -> each 8 s phase keeps its middle 5 s for training

# --- Fair split (course rule) ---
# The ONLY place that defines the test set. Fill with e.g. the last 2 placements once recorded
# (["E05", "E06"]).
# Choose features/models on the train placements only; score the test placements once, at the end.
TEST_PLACEMENTS: list[str] = ["E06"]   # last placement (2026-11-21); E01 = other subject
PATIENT_ID = "P002"       # one person (course rule): other subjects are rejected in QUALITY-REPORT.md

# --- Per-session setup for data/metadata.csv (not in metadata.json, same for every session so far) ---
ELECTRODE_DISTANCE_CM = "not recorded"   # SEN0240 dry electrodes are built into the board
SKIN_PREPARATION = "not recorded"
SENSOR_MODEL = "DFRobot Gravity Analog EMG SEN0240 (OYMotion)"  # PCB front end not working (2026-11-21)
GAIN = "1000"                       # analog gain of the sensor board (SEN0240 datasheet)
ADC_BITS = 12                       # ESP32: 12-bit ADC (0..4095)

# --- Quality check (QUALITY-REPORT.md) ---
GAP_TOLERANCE_S = 1.5 / FS          # t_s step should be 1/FS; a step > 1.5 samples = a missing row
MAX_LENGTH_DEVIATION = 0.02         # reject if the row count is off by > 2 % from the expected 24 000

# --- Model ---
# Features are divided by the rest baseline of the sample, so 1.0 = "like rest".
THRESHOLD_ON = 3.0        # RMS > 3x rest -> contraction
THRESHOLD_OFF = 2.0       # RMS < 2x rest -> rest (hysteresis)
SMOOTH_N = 5              # majority vote over the last N predictions

# --- Metadata choices (dropdowns in the recording app) ---
MUSCLES = ["biceps brachii", "triceps brachii", "flexor carpi radialis", "tibialis anterior", "hamstrings",
           "other"]
SIDES = ["right", "left"]
EFFORTS = ["light", "medium", "strong"]
CONDITIONS = ["fresh", "fatigued"]

# --- Cloud ---
UPLOAD_EVERY_S = 2.0
BLOB_CONTAINER = "signals"
TABLE_SAMPLES = "samples"
TABLE_PREDICTIONS = "predictions"

# --- Paths ---
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_SYNTHETIC = ROOT / "data" / "synthetic"
DATA_DEMO = ROOT / "data" / "demo"      # record.py --source file saves here (replays are not real samples)
MODELS = ROOT / "models"
