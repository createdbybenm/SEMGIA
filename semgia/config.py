"""All tunable constants in one place. Change values here, not in the modules."""

from pathlib import Path

# --- Signal ---
FS = 1000                 # sampling rate in Hz (must match firmware)
RAW_SIGNAL = True         # False if the sensor outputs an envelope (e.g. MyoWare ENV pin)
BANDPASS_HZ = (20, 450)   # only used when RAW_SIGNAL is True
NOTCH_HZ = 50             # mains frequency (Europe)

# --- Windowing ---
WINDOW_S = 0.200          # 200 ms windows
STEP_S = 0.100            # one prediction every 100 ms
WINDOW = int(WINDOW_S * FS)
STEP = int(STEP_S * FS)

# --- Sample protocol: one sample = one continuous 24 s recording ---
REST, CONTRACT = 0, 1
SAMPLE_STEPS = [(REST, 8), (CONTRACT, 8), (REST, 8)]   # (label, seconds)
TRIM_S = 1.5              # windows closer than this to a label change / the start / the end are not "clean"
                          # -> each 8 s phase keeps its middle 5 s for training

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
