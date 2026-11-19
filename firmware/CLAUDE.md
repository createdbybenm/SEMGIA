# firmware/ – microcontroller code

`emg_serial/emg_serial.ino`: Arduino sketch. Reads `A0` at 1000 Hz and prints one integer per line.

## Contract with the PC (frozen – `semgia/sources.py:SerialSource` depends on it)
- Format: `"<value>\n"`, value = raw ADC reading (Arduino Uno: 0–1023), nothing else on the line.
- Baud 115200. Sampling rate = `FS` in `semgia/config.py` (1000). Change both together.
- No debug prints in the data stream (SerialSource silently drops non-number lines, but it costs bandwidth).

## Flashing
Arduino IDE → open `emg_serial/emg_serial.ino` → choose board + port → Upload.
Check: Tools → Serial Plotter at 115200 should show a noisy line that jumps when the muscle contracts.
Then on the PC: `python scripts/record.py --source serial --port /dev/ttyACM0` (Windows: `COM3`).

## Pitfalls
- Use `micros()`-based timing, never `delay()`, or the sampling rate drifts.
- If the sensor board has a raw and an envelope output: wire the **raw** output to A0 and keep `RAW_SIGNAL = True`.
  If only an envelope exists, set `RAW_SIGNAL = False` and note it in MEMORY.md.
- An ESP32 has a 12-bit ADC (0–4095) and different pins → update the comment + MEMORY.md.
- Safety: the subject must only be connected to battery-powered / isolated electronics (laptop on battery, unplugged).
