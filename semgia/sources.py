"""Signal sources. Every source has the same interface:

    read() -> np.ndarray   # all new samples since the last call (may be empty)
    set_cue(cue: int)      # current protocol cue; only MockSource uses it
    close()

So the rest of the app never cares where the data comes from.
"""

import time

import numpy as np
from scipy import signal

from semgia import config


class Source:
    def read(self) -> np.ndarray:
        raise NotImplementedError

    def set_cue(self, cue: int) -> None:
        pass

    def close(self) -> None:
        pass


class MockSource(Source):
    """Fake sEMG in real time: noise at rest, band-limited bursts when cue = CONTRACT.

    gain simulates different electrode placements. fatigue (0..1) makes bursts bigger and
    lower in frequency, like a tired muscle.
    """

    def __init__(self, fs: int = config.FS, gain: float = 1.0, fatigue: float = 0.0,
                 seed: int | None = None):
        self.fs = fs
        self.gain = gain
        self.fatigue = fatigue
        self.rng = np.random.default_rng(seed)
        self.sos = signal.butter(4, [30, 200 - 80 * fatigue], btype="bandpass", fs=fs, output="sos")
        self.zi = signal.sosfilt_zi(self.sos) * 0
        self.cue = config.REST
        self.n = 0
        self.t_last = time.monotonic()

    def set_cue(self, cue: int) -> None:
        self.cue = cue

    def generate(self, n: int) -> np.ndarray:
        """Generate n samples immediately (used for offline mock samples)."""
        burst, self.zi = signal.sosfilt(self.sos, self.rng.normal(size=n), zi=self.zi)
        amp = 60 * self.gain * (1 + 0.5 * self.fatigue) if self.cue == config.CONTRACT else 0
        # like the ESP32: mid-scale offset, no mains hum (the analog notch removes it)
        x = config.ADC_MID + self.rng.normal(scale=4, size=n) + amp * burst
        self.n += n
        return np.clip(np.round(x), 0, 2 ** config.ADC_BITS - 1)

    def read(self) -> np.ndarray:
        now = time.monotonic()
        n = int((now - self.t_last) * self.fs)
        if n == 0:
            return np.empty(0)
        self.t_last += n / self.fs
        return self.generate(n)


class FileSource(Source):
    """Replays the `value` column of a recorded signal.csv in real time (demo fallback)."""

    def __init__(self, csv_path, fs: int = config.FS, loop: bool = True):
        import pandas as pd
        self.values = pd.read_csv(csv_path)["value"].to_numpy(dtype=float)
        self.fs = fs
        self.loop = loop
        self.pos = 0
        self.t_last = time.monotonic()

    def read(self) -> np.ndarray:
        now = time.monotonic()
        n = int((now - self.t_last) * self.fs)
        if n == 0:
            return np.empty(0)
        self.t_last += n / self.fs
        idx = self.pos + np.arange(n)
        if self.loop:
            idx %= len(self.values)
        else:
            idx = idx[idx < len(self.values)]
        self.pos += n
        return self.values[idx]


class SerialSource(Source):
    """Reads one integer per line from the Arduino (see firmware/)."""

    def __init__(self, port: str, baud: int = 115200):
        import serial
        self.ser = serial.Serial(port, baud, timeout=0)
        self.buf = b""

    def read(self) -> np.ndarray:
        self.buf += self.ser.read(self.ser.in_waiting or 1)
        *lines, self.buf = self.buf.split(b"\n")
        values = []
        for line in lines:
            try:
                values.append(float(line.strip()))
            except ValueError:
                pass  # ignore garbage lines (e.g. at connect)
        return np.array(values)

    def close(self) -> None:
        self.ser.close()
