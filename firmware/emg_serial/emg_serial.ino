// SEMGIA firmware: read the EMG sensor on A0 at 1000 Hz and print one integer per line.
// Format (do not change without updating semgia/sources.py):  "<value>\n"   value = 0..1023
// Baud: 115200  (1000 lines/s * max 5 bytes = 5000 B/s, well below the ~11500 B/s limit)

const int EMG_PIN = A0;
const unsigned long PERIOD_US = 1000;  // 1000 Hz -> must match FS in semgia/config.py

unsigned long next_us;

void setup() {
  Serial.begin(115200);
  next_us = micros();
}

void loop() {
  // fixed-rate sampling with micros() instead of delay() -> no timing drift
  if ((long)(micros() - next_us) >= 0) {
    next_us += PERIOD_US;
    Serial.println(analogRead(EMG_PIN));
  }
}
