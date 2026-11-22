// =====================================================================
//  protocolo.h  -  Paquetes ESP-NOW entre el ESP32 del EMG y la ESTACION
// ---------------------------------------------------------------------
//  ESTE ARCHIVO DEBE SER IDENTICO en las dos carpetas:
//     HamShot_EMG/protocolo.h   y   HamShot_Estacion/protocolo.h
//  Si cambias algo aqui, copialo al otro sketch y sube los DOS programas.
//
//  Reparto de tareas (una sola "verdad" por cada dato):
//    EMG       : mide la senal, calcula RMS y % del maximo, guarda la calibracion
//                (reposo/maximo) y sirve la pagina web. NO toma decisiones del juego.
//    ESTACION  : es la maquina. Potes, boton, IR, pantalla, servo. Decide el juego
//                (nivel, tiempo, carga, disparo, puntos) y dirige la calibracion.
//    PAGINA WEB: solo mira (espejo de la maquina) y puede PEDIR una calibracion.
//
//  Flujo:
//    EMG -> ESTACION : PaqueteEMG       50 veces por segundo (activacion en %)
//    ESTACION -> EMG : PaqueteEstado    10 veces por segundo (estado del juego y fase de calibracion)
//    EMG -> ESTACION : PaqueteResultado al terminar una calibracion (reposo y maximo medidos)
//
//  Todos van por broadcast (FF:FF:FF:FF:FF:FF) en el canal WIFI_CANAL: no hace falta poner MACs.
// =====================================================================
#pragma once
#include <stdint.h>

const int WIFI_CANAL = 1;   // el AP del EMG y la estacion DEBEN usar el mismo canal

// "Magic": 4 letras al inicio de cada paquete para saber de que tipo es.
// Se cambio el numero (EMG2, EST2, RES2) para que un programa viejo no se confunda.
const uint32_t MAGIC_EMG       = 0x32474D45;   // "EMG2"
const uint32_t MAGIC_ESTADO    = 0x32545345;   // "EST2"
const uint32_t MAGIC_RESULTADO = 0x32534552;   // "RES2"

// Estado general de la estacion
enum EstadoMaquina : uint8_t { MAQ_NORMAL = 0, MAQ_CALIBRAR = 1, MAQ_AJUSTE = 2, MAQ_BORRAR = 3 };

// Paso de la calibracion (lo que se ve en la pantalla de la maquina)
enum PasoCalibracion : uint8_t { PASO_PREP = 0, PASO_REPOSO = 1, PASO_MAXIMO = 2,
                                 PASO_CALCULANDO = 3, PASO_LISTO = 4, PASO_ERROR = 5 };

#pragma pack(push, 1)   // sin huecos entre campos: viajan iguales en los dos ESP32

// EMG -> ESTACION (50 Hz)
struct PaqueteEMG {
  uint32_t magic;          // MAGIC_EMG
  uint32_t seq;            // contador, solo para depurar
  float    pct;            // activacion en % del rango calibrado (0 si no hay calibracion)
  float    rms;            // RMS actual en mV (en la entrada del ADC)
  uint8_t  calibrado;      // 1 = el EMG tiene una calibracion valida
  uint8_t  pedidoCal;      // sube en 1 cada vez que alguien pide calibrar desde la web
                           // (0 = nadie lo ha pedido desde que arranco el EMG)
};

// ESTACION -> EMG (10 Hz y de inmediato cuando cambia el paso de calibracion)
struct PaqueteEstado {
  uint32_t magic;          // MAGIC_ESTADO
  uint32_t seq;
  uint8_t  estado;         // EstadoMaquina
  uint8_t  paso;           // PasoCalibracion (solo vale si estado == MAQ_CALIBRAR)
  uint8_t  restanteS;      // segundos que faltan en el paso actual de calibracion
  uint8_t  nivelPct;       // NIVEL del pote: umbral en % del maximo (10..100)
  uint8_t  tiempoS;        // TIEMPO del pote: segundos a mantener (1..10)
  uint8_t  cargaPct;       // cuanto lleva cargada la catapulta (0..100 %)
  uint8_t  recargando;     // 1 = acaba de disparar y esta esperando
  uint16_t tiros;          // disparos desde que se encendio la maquina
  uint32_t puntaje;        // canastas (IR) de esta partida
  uint32_t highscore;      // record guardado en la maquina
};

// EMG -> ESTACION (al final de la calibracion, se repite mientras la estacion espera)
struct PaqueteResultado {
  uint32_t magic;          // MAGIC_RESULTADO
  uint32_t seq;
  uint8_t  ok;             // 1 = calibracion valida
  float    reposo;         // RMS medio en reposo (mV)
  float    maximo;         // RMS maximo en la contraccion maxima (mV)
};

#pragma pack(pop)

const uint8_t MAC_BROADCAST[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
