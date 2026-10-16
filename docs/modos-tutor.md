# Modos del tutor y plan de parciales del Margen

Versión de política: `tutorModes-1` (`tutor_modes.POLICY_VERSION`). Todo el cálculo
es **local y determinista**: no hay llamadas a proveedores ni azar en la decisión
de modo ni en el plan. Cada decisión devuelve los motivos que la producen. La
regla de evaluación rigurosa (`docs/evaluacion-rigurosa.md`) se aplica siempre en
cualquier modo. La validez del control no acredita la validez semántica del tutor.

Alcance: **todo el Margen seleccionado** (todos los pliegos, sin el tutorial
`primer-trazo`). Cada pliego conserva su base y sus IDs; los targets son
compuestos `roomId|courseId|eventId` y `roomId|courseId|lessonId` para evitar
colisiones.

## Modos

| Modo | Qué exige | Conserva | Nunca |
|---|---|---|---|
| Flexible | Comprobación breve con evidencia textual del estudiante para avanzar | pendientes, ayudas, criterios no logrados | declarar dominio no acreditado |
| Estricto | Comprensión con evidencia real por criterio, cita breve incluida | incertidumbre como `uncertain`/`pending` | acreditar dominio por longitud, estilo o coincidencia literal |
| Extremo | Transferencia a un caso nuevo, contraejemplos y defensa ante objeciones, adaptado al tema | exige explicitar qué evidencia falta | hostilidad, checklist rígida universal, pesar por longitud o estilo |

Garantía transversal (`tutor_modes.GATE_CLAUSE`): **adaptar la modalidad no
debilita la puerta de evidencia**. Flexible conserva los pendientes, ayudas y
criterios no logrados tal como están: nunca se marca `independent` inventado.
Las respuestas breves y las paráfrasis valen cuando cubren el criterio; la
longitud, el estilo, la confianza y el acuerdo con el tutor no son evidencia.
Tras dos intentos sin progreso se explica y se comprueba transferencia con un
caso distinto.

`mode_prompt(mode)` devuelve las instrucciones que deben **preceder a la
generación** del tutor (API y MCP), no sólo metadatos: sólo adjuntar `tutorMode`
en la respuesta no cambia el comportamiento del modelo.

## Preferencia del alumno

- **Manual**: el alumno fija `flexible`/`strict`/`extreme`. Es un override
  persistente: la política automática no lo reemplaza (sin rebote).
- **Auto**: la política decide `effectiveMode` con datos reales de todo el Margen:
  compromisos `kind exam|deadline` con fecha, preparación acreditada por temario,
  dificultad personal por historial (intentos, respuestas con ayuda,
  incertidumbre), autorreporte aparte (errores/`needsPractice` de los apuntes) y
  **presión de tiempo medida** (minutos requeridos vs declarados antes del plazo).

La preferencia se guarda **por Margen canónico** (`store_path`:
`server.DATA/tutor-modes/margen-<sha1>.json`, clave derivada de la ruta resuelta
del Margen elegido), no en una fila compartida entre Margenes distintos.

### Cambio automático de modo (Q1 confirmada)

En auto, si un parcial o entrega está dentro de **7 días** con preparación
incierta o debajo de **0.5** acreditado, o con presión de tiempo medida, el modo
efectivo baja automáticamente a **Flexible** para poder avanzar conservando
pendientes. El aviso:

- explicita los motivos (qué compromiso, cuántos días, minutos requeridos vs
  declarados),
- **no** se repite en cada render: se entrega una vez por cambio real
  (`evaluate_mode` + `acknowledge_notice`) y guarda el modo **anterior real**
  (en la primera visita `last_mode` es `None`: no hay aviso ni modo supuesto),
- ofrece volver/cambiar; el override manual persiste hasta reactivar auto.

Si no hay presión ni parciales cercanos sin acreditar, la política usa
`strict`/`extreme` con sus motivos. Faltan datos (minutos sin declarar) → se
declara incertidumbre y **no** se inventa urgencia.

## Plan global de parciales

- Solo fechas reales: eventos de calendario `kind exam|deadline` de cada pliego.
  Los apuntes con `study.parcialDate` entran como fecha **declarada por el
  alumno** (`kind: 'study'`, alcance a organizar por el MCP de autoría). Los
  apuntes con materia y sin fecha van a `plan.undated` como «sin fecha», sin
  urgencia ficticia.
- Temario: `confirmed` > `proposed` > materia completa; sin confirmación se
  declara la incertidumbre. `save_exam_topics` valida `lessonIds`/`noteIds`
  existentes, exige revisión y no acepta listas vacías. El MCP de autor propone;
  el alumno confirma (UI o MCP de tutor).
- **Disponibilidad global**: los minutos declarados (weekday/weekend/overrides)
  se contabilizan **una sola vez por día de todo el Margen**. Si los pliegos
  declaran valores distintos, se usa el menor y se listan las fuentes.
- **Asignación real de minutos**: un único presupuesto diario compartido. El
  orden de trabajo es: primero las ediciones del alumno (en su orden), después el
  ranking automático por **puntaje explicable** (proximidad + brecha sin dominar +
  dificultad por evidencia + errores/`needsPractice` declarados + tipo). Cada
  tarea consume sólo días dentro de su propia ventana de deadline, así dos
  parciales el mismo día nunca usan los mismos minutos: invertir la prioridad
  invierte la asignación, no sólo el orden de la lista.
- **Emergencia (Q4)**: si lo asignado no alcanza lo requerido, el plan lo marca,
  cubre hasta el presupuesto y deja lo **postergado explícito** («no acredita
  dominio»). Sin minutos declarados no se afirma urgencia: se declara.
- Incertidumbres declaradas, nunca resueltas por invento: temario sin confirmar,
  lecciones sin minutos, fecha inválida, pliego ilegible, pliegos sin calendario.

## Rol del calendario

`calendar_store.py` centraliza la semántica con helpers **puros** (sin tocar
datos): `commitments(events)` devuelve solo los `kind exam|deadline` con fecha,
ordenados; `study_dates(notes)` devuelve las fechas de parcial declaradas en
apuntes, solo `YYYY-MM-DD` válidas y nunca inferidas. El plan global los usa
para no hardcodear "parcial/entrega" en cada módulo ni aceptar fechas inventadas.

## Roles y persistencia

- **MCP de autoría** (`author_mcp.py`): organiza materias/lecciones/temarios y
  fechas de todo el Margen (`global_courses_overview`, `all_room_events`,
  `propose_exam_topics`, `exam_topics_overview`, `global_plan_overview`) y su
  `author_brief` incluye `tutorMode` (instrucciones antes de generar).
- **MCP de tutor** (`tutor_mcp.py`): consume el plan y la política
  (`tutor_mode_overview`, `global_study_plan`, `list_exam_topics`), registra el
  modo efectivo en cada brief/respuesta y cambia la preferencia sólo por pedido
  del alumno (`tutor_set_mode`), confirmando temarios propuestos
  (`confirm_exam_topic`). Nunca propone temarios ni fechas.
- Un único archivo JSON por Margen (ver `store_path`) con preferencia, último
  modo efectivo, aviso pendiente, temarios y ediciones del plan. El snapshot y
  respaldo ya incluyen el payload crudo de modos vía `export_payload` /
  `import_payload` (validan `format` antes de escribir).

## UI

`web/tutor-modes.js` + `web/tutor-modes.css`: panel de preferencia, modo
efectivo con motivos, aviso de cambio automático, plan global ordenable
(las flechas persisten el nuevo orden y el servidor recalcula la asignación).
`web/plan.js` agrega la pestaña **Parciales**. `POST /api/tutor-modes` (acción
`overview`) ya devuelve el plan global (`build_global_plan`) para la UI; si el
hook HTTP del integrador todavía no existe, el fallback muestra los parciales del
pliego actual y lo declara, sin inventar fechas.
