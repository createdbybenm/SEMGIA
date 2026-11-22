# Hoja de consentimiento informado (SEMGIA)

Se imprime y se firma **en papel**. El nombre y la firma solo existen en esta hoja, que guarda una persona del equipo.
En el repositorio y en Azure la persona solo aparece con su seudónimo (por ejemplo `P002`).

**Proyecto:** SEMGIA, proyecto escolar de la materia M6 Machine Learning and IoT Apps (Tecnológico de Monterrey).
Es un prototipo de investigación, **no** es un dispositivo médico.

**Qué se mide:** la actividad eléctrica del músculo (sEMG) de los isquiotibiales derechos, con un sensor de superficie
(DFRobot SEN0240) que se coloca sobre la piel. No hay agujas ni corriente hacia el cuerpo. Cada grabación dura 24 s:
reposo 8 s, contracción 8 s, reposo 8 s, siguiendo indicaciones en pantalla.

**Para qué:** entrenar un modelo que detecte si el músculo está contraído o en reposo.

**Qué se guarda:** la señal del sensor y datos técnicos de cada grabación (fecha, colocación, esfuerzo, fatiga),
con un seudónimo. **No** se guardan nombre, fecha de nacimiento, fotos de la cara ni otros datos que te identifiquen.
Las fotos de los electrodos no muestran la cara ni tatuajes.

**Dónde se guarda:** en un repositorio privado de GitHub y en Microsoft Azure (región de la Unión Europea),
hasta el final del proyecto. Son datos personales sensibles de salud (LFPDPPP), por eso se guardan con seudónimo.

**Tus derechos:** participar es voluntario. Puedes parar en cualquier momento y pedir que se borren tus grabaciones
sin dar razones (`scripts/delete_sample.py` borra la grabación local, en Azure y en las tablas).

**Contacto:** el equipo SEMGIA (el contacto se escribe a mano en la hoja impresa).

---

Leí esta hoja, entendí lo que se mide y dónde se guarda, y acepto participar.

Seudónimo asignado: ________   Fecha: ____________

Firma del participante: ______________________   Firma de quien graba (operador): ______________________
