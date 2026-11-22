/*
  HamShot - ESP32 del EMG (unidad que lleva el paciente)
  ---------------------------------------------------------------
  QUE HACE ESTE ESP32
    1. Lee la senal del filtro analogico (PCB) a 1000 muestras por segundo.
    2. Quita el offset DC y calcula el RMS en una ventana deslizante de 100 ms.
    3. Convierte el RMS en % del rango calibrado (0 % = reposo, 100 % = maximo).
    4. Manda ese % a la ESTACION (la maquina) por ESP-NOW, 50 veces por segundo.
    5. Mide el reposo y el maximo cuando la ESTACION se lo ordena (calibracion).
    6. Crea su propia red WiFi y sirve la pagina web del fisioterapeuta.

  QUE NO HACE (lo hace la ESTACION)
    - No decide cuando dispara la catapulta, no lee potes ni boton de la maquina.
    - No lleva la cuenta de puntos ni tiros: solo los recibe y los muestra en la web.
    - No decide cuando empieza ni cuanto dura cada paso de la calibracion.

  PAGINA WEB (espejo de la maquina)
    Red WiFi: AP_SSID / AP_PASS (abajo)  ->  abrir  http://192.168.4.1
    La pagina solo muestra datos. Su boton "Recalibrar" solo PIDE la calibracion:
    la estacion la ejecuta igual que si alguien apretara el boton de la maquina.

  ARCHIVOS DE ESTE SKETCH
    HamShot_EMG.ino  (este)
    protocolo.h      (paquetes ESP-NOW; IDENTICO al de la estacion)
    pagina.h         (HTML + JavaScript de la pagina web)
*/

#include <WiFi.h>
#include <WebServer.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include "protocolo.h"
#include "pagina.h"

// ======================= CONFIGURACION =======================
const int   PIN_EMG    = 34;   // DEBE ser ADC1 (GPIO 32-39). ADC2 NO funciona con WiFi activo.
const int   PIN_LED    = 2;    // LED integrado
const int   PIN_BOTON  = 0;    // boton BOOT -> pedir calibracion (igual que el boton de la web)

const char* AP_SSID    = "SEMGIA-EMG";
const char* AP_PASS    = "fisio1234";   // minimo 8 caracteres

const int   FS_HZ       = 1000;   // frecuencia de muestreo (Hz)
const int   VENTANA_RMS = 100;    // muestras en la ventana RMS -> 100 ms
const int   DECIMACION  = 20;     // 1000 / 20 = 50 puntos por segundo para la web
const float ALFA_DC     = 0.002f; // seguimiento del offset DC (constante de tiempo ~0.5 s, ~0.3 Hz)
const float MIN_RANGO_MV = 10.0f; // si (maximo - reposo) < esto, la calibracion se rechaza

const uint32_t T_ENVIO_EMG_MS     = 20;    // PaqueteEMG cada 20 ms (50 Hz)
const uint32_t T_ENVIO_RES_MS     = 100;   // PaqueteResultado cada 100 ms mientras la estacion espera
const uint32_t MAQUINA_TIMEOUT_MS = 1000;  // sin PaqueteEstado tanto tiempo -> "sin conexion con la maquina"
// =============================================================

// ------------- Calibracion (la guarda el EMG, la dirige la estacion) -------------
volatile bool  calibrado   = false;
volatile float nivelReposo = 0;      // RMS medio en reposo (mV)
volatile float nivelMax    = 0;      // RMS maximo (mV)

// Resultado de la ultima calibracion, para mandarlo a la estacion
volatile bool  resultadoListo = false;
volatile bool  resultadoOk    = false;
volatile float resultadoReposo = 0, resultadoMax = 0;

// ------------- Ultimo estado recibido de la estacion -------------
volatile uint32_t maqUltimoMs = 0;
volatile bool     maqAlguno   = false;
volatile uint8_t  maqEstado   = MAQ_NORMAL;
volatile uint8_t  maqPaso     = PASO_PREP;
volatile uint8_t  maqRestante = 0;
volatile uint8_t  maqNivelPct = 70;   // valor de arranque hasta que llegue el primer paquete
volatile uint8_t  maqTiempoS  = 1;
volatile uint8_t  maqCargaPct = 0;
volatile uint8_t  maqRecargando = 0;
volatile uint16_t maqTiros    = 0;
volatile uint32_t maqPuntaje  = 0;
volatile uint32_t maqHighscore = 0;

// ------------- Pedido de calibracion (web o boton BOOT) -------------
volatile uint8_t pedidoCal = 0;      // sube en 1 por cada pedido; viaja en cada PaqueteEMG

// ------------- Procesamiento (solo lo usa la tarea de muestreo) -------------
float  bufVentana[VENTANA_RMS] = {0};
int    posBuf = 0;
double sumaVentana = 0;
float  dc = 0;
double sumaReposo = 0;
uint32_t nReposo = 0;
float  picoMax = 0;
int    contDecim = 0;
int    pasoPrevio = -1;              // para detectar el cambio de paso de calibracion

volatile float rmsActual = 0;        // ultimo RMS (mV)
volatile float pctActual = 0;        // ultimo % del rango calibrado
volatile bool  sobreUmbral = false;  // pct >= NIVEL de la maquina (misma regla que usa la estacion)

// ------------- Buffer circular para la web (50 Hz, ~10 s) -------------
// Cada punto guarda tambien el estado de la maquina en ese momento, para que el CSV
// muestre cuando cargo, cuando disparo (tiros) y cuando entro una canasta.
struct Punto { float rms; float pct; uint8_t act; uint8_t carga; uint16_t tiros; uint16_t canastas; };
const int RB_N = 512;
Punto rb[RB_N];
volatile uint32_t rbTotal = 0;

// Buffer circular de la EMG CRUDA del ADC (cuentas 0..4095, 12 bits, reposo ~2048), 1000 muestras/s, ~8 s.
// Es la salida del filtro analogico tal cual la lee el ADC (mismo formato que el puerto serie de SEMGIA).
// Es la senal que la web guarda en las muestras SEMGIA (24 s): 8 s de reserva para que
// un navegador lento (pestana en segundo plano, WiFi ocupado) no pierda datos.
const int RAW_N = 8192;          // potencia de 2 (16 KB de RAM)
const int RAW_MAX_PEDIDO = 1000; // como maximo 1 s de EMG por respuesta de /datos
int16_t rawBuf[RAW_N];
volatile uint32_t rawTotal = 0;
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

WebServer server(80);

bool maquinaConectada() {
  uint32_t ultimo = maqUltimoMs;     // se lee antes de millis() para que la resta no de la vuelta
  return maqAlguno && (millis() - ultimo < MAQUINA_TIMEOUT_MS);
}

// =====================================================================
//                  CALIBRACION (sigue los pasos de la estacion)
// =====================================================================
// Se llama con cada muestra. La estacion dice en que paso esta; aqui solo se mide.
void medirCalibracion(float rms) {
  int paso = (maqEstado == MAQ_CALIBRAR) ? (int)maqPaso : -1;   // -1 = no se esta calibrando

  if (paso != pasoPrevio) {                     // acaba de cambiar el paso
    if (paso == PASO_PREP || paso == PASO_REPOSO) resultadoListo = false;   // calibracion nueva
    if (paso == PASO_REPOSO) { sumaReposo = 0; nReposo = 0; }
    if (paso == PASO_MAXIMO) { picoMax = 0; }
    if (paso == PASO_CALCULANDO && !resultadoListo) {
      // Termino la contraccion maxima: calcular el resultado
      float reposo = nReposo ? (float)(sumaReposo / nReposo) : 0;
      float maximo = picoMax;
      bool  ok     = (nReposo > 0) && (maximo - reposo >= MIN_RANGO_MV);
      resultadoReposo = reposo;
      resultadoMax    = maximo;
      resultadoOk     = ok;
      if (ok) {                                 // solo se reemplaza la calibracion si es valida
        nivelReposo = reposo;
        nivelMax    = maximo;
        calibrado   = true;
      }
      resultadoListo = true;
    }
    pasoPrevio = paso;
  }

  if (paso == PASO_REPOSO) { sumaReposo += rms; nReposo++; }
  if (paso == PASO_MAXIMO && rms > picoMax) picoMax = rms;
}

// =====================================================================
//                    PROCESAMIENTO DE CADA MUESTRA
// =====================================================================
void procesarMuestra() {
  int   cuenta = analogRead(PIN_EMG);                // 0..4095: lo que guarda SEMGIA (signal.csv)
  float x = (float)analogReadMilliVolts(PIN_EMG);    // mV calibrados: RMS, calibracion y juego

  // 1) Quitar el offset DC (filtro pasa-altas digital muy lento)
  dc += (x - dc) * ALFA_DC;
  float v = x - dc;

  // 2) RMS deslizante de 100 ms: se suma el cuadrado nuevo y se resta el mas viejo
  float c = v * v;
  sumaVentana += c - bufVentana[posBuf];
  bufVentana[posBuf] = c;
  posBuf = (posBuf + 1) % VENTANA_RMS;
  if (sumaVentana < 0) sumaVentana = 0;         // por redondeo nunca debe ser negativa
  float rms = sqrtf(sumaVentana / VENTANA_RMS);

  // Guardar la cuenta cruda del ADC para la web (grafica de EMG y muestras SEMGIA)
  portENTER_CRITICAL(&mux);
  rawBuf[rawTotal % RAW_N] = (int16_t)cuenta;
  rawTotal = rawTotal + 1;
  portEXIT_CRITICAL(&mux);

  // 3) Calibracion (solo mide si la estacion esta calibrando)
  medirCalibracion(rms);

  // 4) % del rango calibrado
  float pct = 0;
  if (calibrado) {
    pct = 100.0f * (rms - nivelReposo) / (nivelMax - nivelReposo);
    if (pct < 0)   pct = 0;
    if (pct > 200) pct = 200;
  }

  rmsActual   = rms;
  pctActual   = pct;
  sobreUmbral = calibrado && maquinaConectada() && (maqEstado != MAQ_CALIBRAR)
                && (pct >= maqNivelPct);        // solo para mostrar en la web; la estacion decide

  // 5) Guardar 1 de cada 20 muestras para la web
  if (++contDecim >= DECIMACION) {
    contDecim = 0;
    Punto p = {rms, pct, (uint8_t)(sobreUmbral ? 1 : 0), maqCargaPct, maqTiros, (uint16_t)maqPuntaje};
    portENTER_CRITICAL(&mux);
    rb[rbTotal % RB_N] = p;
    rbTotal = rbTotal + 1;
    portEXIT_CRITICAL(&mux);
  }
}

// Tarea propia en el nucleo 1: muestrea cada 1 ms aunque la web este ocupada
void tareaMuestreo(void*) {
  TickType_t periodo = pdMS_TO_TICKS(1000 / FS_HZ);
  if (periodo == 0) periodo = 1;
  TickType_t ultimo = xTaskGetTickCount();
  for (;;) {
    procesarMuestra();
    vTaskDelayUntil(&ultimo, periodo);
  }
}

// =====================================================================
//                               ESP-NOW
// =====================================================================
// Recibe el estado de la maquina. Corre en la tarea de WiFi: solo copia datos.
void procesarPaquete(const uint8_t* data, int len) {
  if (len != (int)sizeof(PaqueteEstado)) return;
  PaqueteEstado p;
  memcpy(&p, data, sizeof(p));
  if (p.magic != MAGIC_ESTADO) return;
  maqEstado     = p.estado;
  maqPaso       = p.paso;
  maqRestante   = p.restanteS;
  maqNivelPct   = p.nivelPct;
  maqTiempoS    = p.tiempoS;
  maqCargaPct   = p.cargaPct;
  maqRecargando = p.recargando;
  maqTiros      = p.tiros;
  maqPuntaje    = p.puntaje;
  maqHighscore  = p.highscore;
  maqUltimoMs   = millis();
  maqAlguno     = true;
}

#if ESP_ARDUINO_VERSION_MAJOR >= 3
void alRecibir(const esp_now_recv_info_t* info, const uint8_t* data, int len) {
#else
void alRecibir(const uint8_t* mac, const uint8_t* data, int len) {
#endif
  procesarPaquete(data, len);
}

void enviarEMG() {
  static uint32_t seq = 0;
  PaqueteEMG p;
  p.magic     = MAGIC_EMG;
  p.seq       = seq++;
  p.pct       = pctActual;
  p.rms       = rmsActual;
  p.calibrado = calibrado ? 1 : 0;
  p.pedidoCal = pedidoCal;
  esp_now_send(MAC_BROADCAST, (const uint8_t*)&p, sizeof(p));
}

void enviarResultado() {
  static uint32_t seq = 0;
  PaqueteResultado p;
  p.magic  = MAGIC_RESULTADO;
  p.seq    = seq++;
  p.ok     = resultadoOk ? 1 : 0;
  p.reposo = resultadoReposo;
  p.maximo = resultadoMax;
  esp_now_send(MAC_BROADCAST, (const uint8_t*)&p, sizeof(p));
}

// Pedir calibracion (web o boton BOOT). Nunca vale 0 despues de un pedido,
// porque 0 significa "nadie ha pedido nada desde que arranco el EMG".
void pedirCalibracion() {
  uint8_t n = pedidoCal + 1;
  if (n == 0) n = 1;
  pedidoCal = n;
  Serial.println("Calibracion pedida -> se avisa a la maquina");
}

// =====================================================================
//                                  WEB
// =====================================================================
// Codigo de estado para la pagina (el texto de cada uno esta en pagina.h, ESTADOS[])
//   0 sin conexion con la maquina   1 conectado pero sin calibrar
//   2..7 calibrando (PREP, REPOSO, MAXIMO, CALCULANDO, LISTO, ERROR)   8 listo / jugando
int estadoParaWeb() {
  if (!maquinaConectada())      return 0;
  if (maqEstado == MAQ_CALIBRAR) return 2 + maqPaso;
  if (!calibrado)               return 1;
  return 8;
}

void hRaiz() {
  server.send(200, "text/html", PAGINA_HTML);
}

// Devuelve en JSON los puntos nuevos desde "desde" (RMS, 50 Hz), las muestras nuevas
// desde "desdeR" (EMG filtrada, 1 kHz) y el estado de la maquina
void hDatos() {
  uint32_t desde = server.hasArg("desde") ? strtoul(server.arg("desde").c_str(), nullptr, 10) : 0;
  uint32_t desdeR = server.hasArg("desdeR") ? strtoul(server.arg("desdeR").c_str(), nullptr, 10) : 0;
  static Punto copia[RB_N];
  static int16_t copiaR[RAW_MAX_PEDIDO];
  uint32_t total;
  int n, nR;

  portENTER_CRITICAL(&mux);
  total = rbTotal;
  uint32_t masViejo = total > RB_N ? total - RB_N : 0;
  if (desde > total || desde < masViejo) desde = masViejo;   // reinicio o cliente atrasado
  n = (int)(total - desde);
  if (n > 250) n = 250;
  for (int i = 0; i < n; i++) copia[i] = rb[(desde + i) % RB_N];
  uint32_t totalR = rawTotal;
  uint32_t masViejoR = totalR > RAW_N ? totalR - RAW_N : 0;
  if (desdeR > totalR || desdeR < masViejoR) desdeR = masViejoR;
  nR = (int)(totalR - desdeR);
  if (nR > RAW_MAX_PEDIDO) nR = RAW_MAX_PEDIDO;              // el resto llega en el proximo pedido
  for (int i = 0; i < nR; i++) copiaR[i] = rawBuf[(desdeR + i) % RAW_N];
  portEXIT_CRITICAL(&mux);

  bool  cal = calibrado;
  float rep = nivelReposo, mx = nivelMax;
  int   niv = maqNivelPct;
  float thr = rep + (niv / 100.0f) * (mx - rep);              // umbral de la maquina en mV

  String j;
  j.reserve(360 + n * 36 + nR * 6);
  j += "{\"st\":";    j += estadoParaWeb();
  j += ",\"rt\":";    j += (int)maqRestante;
  j += ",\"cal\":";   j += cal ? 1 : 0;
  j += ",\"rest\":";  j += String(rep, 1);
  j += ",\"max\":";   j += String(mx, 1);
  j += ",\"thr\":";   j += String(thr, 1);
  j += ",\"pa\":";    j += niv;
  j += ",\"tie\":";   j += (int)maqTiempoS;
  j += ",\"car\":";   j += (int)maqCargaPct;
  j += ",\"rec\":";   j += (int)maqRecargando;
  j += ",\"tiros\":"; j += (unsigned)maqTiros;
  j += ",\"pts\":";   j += (unsigned long)maqPuntaje;
  j += ",\"hs\":";    j += (unsigned long)maqHighscore;
  j += ",\"i0\":";    j += desde;
  j += ",\"idx\":";   j += (uint32_t)(desde + n);
  j += ",\"r0\":";   j += desdeR;
  j += ",\"ridx\":"; j += (uint32_t)(desdeR + nR);
  j += ",\"r\":[";
  for (int i = 0; i < nR; i++) { if (i) j += ','; j += (int)copiaR[i]; }
  j += "]";
  j += ",\"d\":[";
  for (int i = 0; i < n; i++) {
    if (i) j += ',';
    j += '[';
    j += String(copia[i].rms, 1); j += ',';
    j += String(copia[i].pct, 1); j += ',';
    j += (int)copia[i].act;       j += ',';
    j += (int)copia[i].carga;     j += ',';
    j += (unsigned)copia[i].tiros; j += ',';
    j += (unsigned)copia[i].canastas;
    j += ']';
  }
  j += "]}";
  server.send(200, "application/json", j);
}

// La web solo PIDE la calibracion; la maquina la ejecuta
void hCalibrar() {
  pedirCalibracion();
  server.send(200, "text/plain", "ok");
}

// =====================================================================
//                                EXTRAS
// =====================================================================
// LED: fijo = sobre el umbral · lento = sin calibrar · rapido = sin maquina
void actualizarLed(uint32_t t) {
  bool on;
  if (!maquinaConectada())          on = (t / 100) % 2;
  else if (maqEstado == MAQ_CALIBRAR) on = (t / 250) % 2;
  else if (!calibrado)              on = (t / 1000) % 2;
  else                              on = sobreUmbral;
  digitalWrite(PIN_LED, on);
}

void imprimirCambios() {
  static int stPrev = -1;
  int st = estadoParaWeb();
  if (st == stPrev) return;
  stPrev = st;
  switch (st) {
    case 0: Serial.println("Sin conexion con la maquina (estacion)"); break;
    case 1: Serial.println("Maquina conectada. Falta calibrar (boton de la maquina, web o BOOT)"); break;
    case 3: Serial.println("Calibracion: midiendo REPOSO..."); break;
    case 4: Serial.println("Calibracion: midiendo MAXIMO..."); break;
    case 6:
    case 8:
      if (calibrado) Serial.printf("Calibrado: reposo %.1f mV | maximo %.1f mV\n",
                                   (float)nivelReposo, (float)nivelMax);
      break;
    case 7: Serial.println("Calibracion rechazada (revise electrodos)"); break;
  }
}

// =====================================================================
//                                 SETUP
// =====================================================================
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BOTON, INPUT_PULLUP);
  analogReadResolution(12);

  // Estimacion inicial del offset para que el filtro arranque centrado
  double s = 0;
  for (int i = 0; i < 200; i++) { s += analogReadMilliVolts(PIN_EMG); delay(1); }
  dc = s / 200.0;
  Serial.printf("\nOffset inicial medido: %.0f mV\n", dc);

  // WiFi propio (punto de acceso) en un canal fijo: la estacion usa el mismo
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS, WIFI_CANAL);
  Serial.printf("Red WiFi: %s  (clave: %s)\nAbra: http://%s\n",
                AP_SSID, AP_PASS, WiFi.softAPIP().toString().c_str());

  // ESP-NOW por broadcast (no hace falta conocer la MAC de la estacion)
  if (esp_now_init() != ESP_OK) {
    Serial.println("ERROR iniciando ESP-NOW");
  } else {
    esp_now_register_recv_cb(alRecibir);
    esp_now_peer_info_t peer = {};
    memcpy(peer.peer_addr, MAC_BROADCAST, 6);
    peer.channel = WIFI_CANAL;
    peer.ifidx   = WIFI_IF_AP;
    peer.encrypt = false;
    if (esp_now_add_peer(&peer) != ESP_OK) Serial.println("ERROR agregando broadcast ESP-NOW");
  }

  server.on("/", hRaiz);
  server.on("/datos", hDatos);
  server.on("/cal", HTTP_POST, hCalibrar);
  server.begin();

  xTaskCreatePinnedToCore(tareaMuestreo, "emg", 4096, nullptr, 3, nullptr, 1);
}

// =====================================================================
//                                 LOOP
// =====================================================================
void loop() {
  server.handleClient();
  uint32_t ahora = millis();

  // Activacion para la maquina: 50 veces por segundo
  static uint32_t tEmg = 0;
  if (ahora - tEmg >= T_ENVIO_EMG_MS) { tEmg = ahora; enviarEMG(); }

  // Resultado de calibracion: se repite mientras la maquina siga esperando
  static uint32_t tRes = 0;
  bool esperando = maquinaConectada() && maqEstado == MAQ_CALIBRAR && maqPaso == PASO_CALCULANDO;
  if (esperando && resultadoListo && ahora - tRes >= T_ENVIO_RES_MS) { tRes = ahora; enviarResultado(); }

  // Boton BOOT -> pedir calibracion
  static uint32_t tBoton = 0;
  if (digitalRead(PIN_BOTON) == LOW && ahora - tBoton > 1000) {
    tBoton = ahora;
    pedirCalibracion();
  }

  imprimirCambios();
  actualizarLed(ahora);
  delay(2);
}
