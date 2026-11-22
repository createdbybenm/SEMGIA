# firmware/ – microcontroller code

| Folder | Board | Use |
|---|---|---|
| `semgia_emg/` | **ESP32** | **Main recording path.** Samples GPIO 34 at 1 kHz, Wi-Fi hotspot + web page for calibration and samples |
| `emg_serial/` | Arduino Uno | Backup only: prints one ADC value per line for `record.py --source serial` |

`semgia_emg/` = one ESP32, nothing else. `semgia_emg.ino` only samples and serves raw ADC counts (`GET /datos`);
`pagina.h` (the web page, runs in the browser) does everything else: live RMS + % activation, calibration
(prepare 3 s / rest 5 s / max 5 s → rest + max RMS), the 24 s samples and the downloads for `import_web.py`.

## Sensor wiring (DFRobot Gravity Analog EMG Sensor SEN0240)
| Sensor cable | Pin label on sensor | ESP32 pin |
|---|---|---|
| **blue** | `A` – analog signal 0–3.0 V | **GPIO 34** (`PIN_EMG`, ADC1) |
| **red** | `+` – supply 3.3–5.5 V | **3V3** (or 5V/VIN when powered by USB) |
| **black** | `-` – 0 V | **GND** |
- The output is **analog** (amplified ×1000, 20–500 Hz, centred on 1.5 V ≈ 1860 counts), not digital and not an
  envelope → analog pin, `RAW_SIGNAL = True`.
- ADC1 pins only (GPIO 32–39). ADC2 pins do not work while Wi-Fi is on. GPIO 34–39 are input-only, which is fine.
- Colours: Gravity standard. If your cable differs, follow the `A / + / -` labels on the sensor board.
- Dry electrodes along the muscle direction, strap tight on bare skin. No gel.
- **Safety:** the person may only be connected to battery-powered electronics: laptop unplugged from mains while
  the sensor is on the skin.

## Flashing `semgia_emg`
1. Arduino IDE with the ESP32 core (tested: esp32 3.3.12). No extra libraries.
2. File → Open → `firmware/semgia_emg/semgia_emg.ino`. Board **ESP32 Dev Module**, the board's COM port → Upload.
   Stuck at `Connecting....` → hold **BOOT** until it starts.
3. Serial Monitor 115200: prints the Wi-Fi name and `http://192.168.4.1`, then every 10 s `samples/s: 1000` and
   the last value (rest ≈ 1860 with the SEN0240; ~0 or ~4095 = wiring problem).
4. Laptop: Wi-Fi `SEMGIA-EMG` (password `fisio1234`, local hotspot only) → `http://192.168.4.1`.
5. Check: the live graph moves when the muscle contracts. Recording steps: `docs/protocol.md`.
Compile check without a board (used for PRs): Arduino IDE's bundled `arduino-cli compile --fqbn esp32:esp32:esp32 firmware/semgia_emg`.

## Contracts (change only together with the Python side)
- Web page downloads → `scripts/import_web.py` (`semgia/recorder.py:save_web_sample`): format `semgia-sample-1` /
  `semgia-calib-2`, `values` = raw 12-bit ADC counts (24 000 per sample, 13 000 per calibration). Page constants
  marked `= config.X` (`PASOS`, `PASOS_CAL`, `VENT`, dropdowns, `N_PLAN`, …) must match `semgia/config.py`:
  `tests/test_sources_storage.py::test_web_page_constants_match_config` fails otherwise.
- Serial path (`emg_serial`, frozen – `semgia/sources.py:SerialSource`): `"<value>\n"`, 115200 baud, FS = 1000.

## Pitfalls
- SEN0240 saturates at 3.0 V ≈ 3720 counts (not 4095): the quality check does not see that. Look at the plot.
- Use `micros()`/timer-based sampling, never `delay()`, or the sampling rate drifts.
- Keep the web page in the foreground during a sample (browser > 8 s behind → sample aborted, repeat it).
