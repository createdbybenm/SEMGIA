# firmware/ – microcontroller code

| Folder | Board | Use |
|---|---|---|
| `HamShot_EMG/` | **ESP32** (EMG board) | **Main recording path.** Samples GPIO 34 at 1 kHz, Wi-Fi hotspot + web page for calibration and samples |
| `emg_serial/` | Arduino Uno | Backup only: prints one ADC value per line for `record.py --source serial` |

`HamShot_EMG/` = `HamShot_EMG.ino` (sampling, Wi-Fi, web server) + `pagina.h` (the web page) + `protocolo.h`
(ESP-NOW packets to the catapult station). The station sketch is **not** in this repo; it is only needed for
"Calibrar colocación" (it runs the rest / max sequence). Samples work without it.

## Sensor wiring (DFRobot Gravity Analog EMG Sensor SEN0240)
| Sensor cable | Pin label on sensor | ESP32 pin |
|---|---|---|
| **blue** | `A` – analog signal 0–3.0 V | **GPIO 34** (`PIN_EMG`, ADC1) |
| **red** | `+` – supply 3.3–5.5 V | **3V3** (or 5V/VIN when powered by USB) |
| **black** | `-` – 0 V | **GND** |
- The output is **analog** (amplified ×1000, 20–500 Hz, nominal centre 1.5 V; measured rest ≈ 1650 counts), not digital and not an
  envelope → analog pin, `RAW_SIGNAL = True`.
- ADC1 pins only (GPIO 32–39). ADC2 pins do not work while Wi-Fi is on. GPIO 34–39 are input-only, which is fine.
- Colours: Gravity standard. If your cable differs, follow the `A / + / -` labels on the sensor board.
- Dry electrodes along the muscle direction, strap tight on bare skin. No gel.
- **Safety:** the person may only be connected to battery-powered electronics: laptop unplugged from mains while
  the sensor is on the skin.

## Flashing `HamShot_EMG`
1. Arduino IDE with the ESP32 core (tested: esp32 3.3.12). No extra libraries.
2. File → Open → `firmware/HamShot_EMG/HamShot_EMG.ino`. Board **ESP32 Dev Module**, the board's COM port → Upload.
   Stuck at `Connecting....` → hold **BOOT** until it starts.
3. Serial Monitor 115200: prints the Wi-Fi name and `http://192.168.4.1`.
4. Laptop: Wi-Fi `SEMGIA-EMG` (password `fisio1234`, local hotspot only) → `http://192.168.4.1`.
5. Check: the live graph moves when the muscle contracts. Recording steps: `docs/protocol.md`.
Compile check without a board (used for PRs): Arduino IDE's bundled `arduino-cli compile --fqbn esp32:esp32:esp32 firmware/HamShot_EMG`.

## Contracts (change only together with the Python side)
- Web page downloads → `scripts/import_web.py` (`semgia/recorder.py:save_web_sample`): format `semgia-sample-1` /
  `semgia-calib-1`, `values` = raw 12-bit ADC counts, 24 000 per sample. Page constants (`PASOS`, `N_MUESTRA`,
  dropdowns `MUSCULOS`, `LADOS`, `ESFUERZOS`, `CONDICIONES`, `N_PLAN`) must match `semgia/config.py`.
- `protocolo.h` must be identical to the station's copy. Changing it = reflash both boards.
- Serial path (`emg_serial`, frozen – `semgia/sources.py:SerialSource`): `"<value>\n"`, 115200 baud, FS = 1000.

## Pitfalls
- SEN0240 saturates at 3.0 V ≈ 3720 counts (not 4095): the quality check does not see that. Look at the plot.
- Use `micros()`/timer-based sampling, never `delay()`, or the sampling rate drifts.
- Keep the web page in the foreground during a sample (browser > 8 s behind → sample aborted, repeat it).
