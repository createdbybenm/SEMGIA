/*
  SEMGIA - ESP32 EMG board (one board, nothing else needed)
  ---------------------------------------------------------------
  WHAT IT DOES
    1. Reads the EMG sensor (DFRobot SEN0240, analog) on GPIO 34, 1000 times per second.
    2. Keeps the last ~8 s of raw 12-bit ADC counts (0..4095) in a ring buffer.
    3. Opens its own Wi-Fi network and serves the recording web page (pagina.h).

  EVERYTHING ELSE HAPPENS IN THE BROWSER (pagina.h)
    Calibration (prepare / rest / max contraction), RMS, % activation, the 24 s samples and
    the downloads for scripts/import_web.py. The board does no signal processing at all:
    it only delivers the raw counts, exactly what ends up in signal.csv.

  WEB API
    GET /                -> the page
    GET /datos?desdeR=N  -> {"fs":1000,"r0":N,"ridx":M,"r":[counts N..M-1]}   (max 1 s per reply)
       If N is too old (browser fell > 8 s behind) or in the future (board restarted),
       r0 != N: the page sees the gap and aborts the running sample / calibration.

  WIRING + FLASHING: firmware/CLAUDE.md
*/

#include <WiFi.h>
#include <WebServer.h>
#include "pagina.h"

// ======================= SETTINGS =======================
const int   PIN_EMG  = 34;     // MUST be ADC1 (GPIO 32-39): ADC2 does not work while Wi-Fi is on
const int   PIN_LED  = 2;      // on-board LED: blinks = running, on = a browser is reading data

const char* AP_SSID  = "SEMGIA-EMG";
const char* AP_PASS  = "fisio1234";   // local hotspot only, min. 8 characters

const int   FS_HZ    = 1000;   // sampling rate = config.FS in semgia/config.py
const int   RAW_N    = 8192;   // ring buffer: ~8 s of reserve for a slow browser (power of 2, 16 KB RAM)
const int   MAX_REPLY = 1000;  // at most 1 s of data per /datos reply
// ========================================================

int16_t rawBuf[RAW_N];
volatile uint32_t rawTotal = 0;          // samples taken since boot
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
volatile uint32_t lastPollMs = 0;        // last /datos request (LED)

WebServer server(80);

// Own task on core 1: one sample every 1 ms, even while the web server is busy
void samplingTask(void*) {
  TickType_t period = pdMS_TO_TICKS(1000 / FS_HZ);
  if (period == 0) period = 1;
  TickType_t last = xTaskGetTickCount();
  for (;;) {
    int16_t v = (int16_t)analogRead(PIN_EMG);
    portENTER_CRITICAL(&mux);
    rawBuf[rawTotal % RAW_N] = v;
    rawTotal = rawTotal + 1;
    portEXIT_CRITICAL(&mux);
    vTaskDelayUntil(&last, period);
  }
}

void handleRoot() {
  server.send(200, "text/html", PAGINA_HTML);
}

void handleData() {
  uint32_t from = server.hasArg("desdeR") ? strtoul(server.arg("desdeR").c_str(), nullptr, 10) : 0;
  static int16_t copy[MAX_REPLY];
  portENTER_CRITICAL(&mux);
  uint32_t total = rawTotal;
  uint32_t oldest = total > RAW_N ? total - RAW_N : 0;
  if (from > total || from < oldest) from = oldest;   // restarted board or browser too far behind
  int n = (int)(total - from);
  if (n > MAX_REPLY) n = MAX_REPLY;                    // the rest comes with the next request
  for (int i = 0; i < n; i++) copy[i] = rawBuf[(from + i) % RAW_N];
  portEXIT_CRITICAL(&mux);

  String j;
  j.reserve(64 + n * 5);
  j += "{\"fs\":";   j += FS_HZ;
  j += ",\"r0\":";   j += from;
  j += ",\"ridx\":"; j += (uint32_t)(from + n);
  j += ",\"r\":[";
  for (int i = 0; i < n; i++) { if (i) j += ','; j += (int)copy[i]; }
  j += "]}";
  server.send(200, "application/json", j);
  lastPollMs = millis();
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  analogReadResolution(12);

  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.printf("\nSEMGIA EMG  |  Wi-Fi: %s  (password: %s)  |  open http://%s\n",
                AP_SSID, AP_PASS, WiFi.softAPIP().toString().c_str());

  server.on("/", handleRoot);
  server.on("/datos", handleData);
  server.begin();

  xTaskCreatePinnedToCore(samplingTask, "emg", 4096, nullptr, 3, nullptr, 1);
}

void loop() {
  server.handleClient();
  uint32_t now = millis();

  // LED: steady while a browser reads data, slow blink otherwise
  uint32_t lastPoll = lastPollMs;
  digitalWrite(PIN_LED, (now - lastPoll < 1000) ? HIGH : ((now / 500) % 2));

  // Every 10 s: real sampling rate + current value (checks FS = 1000 and the wiring)
  static uint32_t tPrint = 0, nPrint = 0;
  if (now - tPrint >= 10000) {
    uint32_t n = rawTotal;
    if (tPrint) Serial.printf("samples/s: %.0f  |  last value: %d (rest should be ~1860)\n",
                              (n - nPrint) * 1000.0 / (now - tPrint), (int)rawBuf[(n - 1) % RAW_N]);
    tPrint = now; nPrint = n;
  }
  delay(2);
}
