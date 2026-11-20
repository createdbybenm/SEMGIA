"""All tunable constants in one place. Change values here, not in the modules."""

from pathlib import Path

# --- Signal ---
FS = 1000                 # sampling rate in Hz (must match firmware)
RAW_SIGNAL = True         # False if the sensor outputs an envelope (e.g. MyoWare ENV pin)
ADC_MID = 2048            # ESP32 mid-scale: where a raw signal sits at rest (only used by MockSource)
# Filtering is analog (20-447 Hz band-pass + 60 Hz notch), no digital filter (Ben 2026-11-19).
# Software only subtracts each window's mean in processing.features (ESP32 offset ~2048).

# --- Windowing ---
WINDOW_S = 0.200          # 200 ms windows
STEP_S = 0.100            # one prediction every 100 ms
WINDOW = int(WINDOW_S * FS)
STEP = int(STEP_S * FS)

# --- Sample protocol: one sample = one continuous 24 s recording ---
REST, CONTRACT = 0, 1
SAMPLE_STEPS = [(REST, 8), (CONTRACT, 8), (REST, 8)]   # (label, seconds)
WARNING_S = 0             # no warning cue before the contraction (open question)
TRIM_S = 1.5              # windows closer than this to a label change / the start / the end are not "clean"
                          # -> each 8 s phase keeps its middle 5 s for training

# --- Fair split (course rule) ---
# The ONLY place that defines the test set. Fill with e.g. the last 2 placements once recorded
# (["E05", "E06"]).
# Choose features/models on the train placements only; score the test placements once, at the end.
TEST_PLACEMENTS: list[str] = []

# --- Per-session setup for data/metadata.csv (not in metadata.json, same for every session so far) ---
ELECTRODE_DISTANCE_CM = "TODO-P1"   # centre-to-centre distance of the two electrodes
SKIN_PREPARATION = "TODO-P1"        # e.g. "alcohol wipe"
SENSOR_MODEL = "TODO-P1"            # e.g. "MyoWare 2.0"
GAIN = "TODO-P1"                    # analog gain of the sensor board
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
MUSCLES = ["biceps brachii", "triceps brachii", "flexor carpi radialis", "tibialis anterior", "other"]
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
MODELS = ROOT / "models"
