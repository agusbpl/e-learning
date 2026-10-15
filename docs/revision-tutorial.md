# Revisión semántica · tutorial 1.0.2 (candidata 0.1.0)

Referencia: `courses/tutorial.json` v1.0.2 (`id: glosa-primer-trazo`, 4 lecciones,
tipo de actividad `open`). Regla aplicada: `docs/evaluacion-rigurosa.md` (2026-10-10.1).

Revisión de DeepSeek V4 Flash (`inkstone/deepseek-v4-flash-0731`), contrastada y ajustada por el coordinador el 2026-10-15. La independencia respecto de la autoría original no está acreditada.

Las «respuestas mínimas» son **REFERENCIA DE AUTORÍA** (respuesta mínima defendible
según el enunciado y la fuente). No son respuestas de alumno ni citas literales.

## Lección 1 · trazo-entrar · «Un lugar para empezar» (`id: trazo-entrar`)

- **Objetivo observable:** distinguir apertura directa de importación como copia
  independiente y elegir según el lugar donde se guardan los cambios.
- **Enunciado:** «¿Qué diferencia hay entre abrir un pliego existente e importar un
  respaldo? Explicá cuál elegirías para seguir trabajando en la misma carpeta.»
- **Rúbrica (2 criterios):** (1) distinguir apertura directa de creación de copia;
  (2) relacionar la elección con el lugar donde se guardarán los cambios.
- **Consistencia enunciado/rúbrica:** coherente. El enunciado pide diferencia + elección
  y la rúbrica cubre ambos. La elección compatible es abrir el existente; se aceptan formulaciones equivalentes.
- **Respuesta mínima [AUTORÍA]:** «Abrir trabaja sobre los datos del pliego; importar
  (ZIP o carpeta) crea una copia independiente. Para seguir en la misma carpeta,
  abriría el pliego existente, así los cambios quedan ahí.»
- **Fuente local exacta:** `courses/tutorial.json` → `lessons[0].blocks[1].text`
  (`trazo-entrar-b2`), contrastado por el coordinador con `rooms.py::room` y `rooms.py::register` (importación en un directorio nuevo).
- **Riesgos de estilo:** no premiar extensión; el criterio 2 exige la relación con el
  lugar de guardado. Contradicción a penalizar: afirmar que importar conserva los
  cambios en la misma carpeta.

## Lección 2 · trazo-mover · «Moverte sin ruido» (`id: trazo-mover`)

- **Objetivo observable:** proponer un recorrido ejecutable con controles/movimientos
  documentados.
- **Enunciado:** «Probá los modos y los comandos. ¿Qué recorrido usarías para ir a
  Notas, volver a Estudiar y abrir el índice?»
- **Rúbrica (1 criterio):** proponer un recorrido ejecutable con los controles o
  movimientos documentados.
- **Consistencia:** coherente. Hay varias rutas válidas; la rúbrica no impone una única.
- **Respuesta mínima [AUTORÍA]:** «g n va a Notas, g e vuelve a Estudiar y g l (o /)
  abre el índice.»
- **Fuente local exacta:** `courses/tutorial.json` → `lessons[1].blocks[0].text`
  (`trazo-mover-b1`). Comandos registrados en `web/keyboard.js::commands` y manejador de `/`. El coordinador precisó que `/` abre el índice en Estudiar y la lista de apuntes en Notas; `g l` abre el índice desde ambos modos.
- **Riesgos:** aceptar cualquier ruta con controles documentados aunque esté
  parafraseada; comprobar la ejecutabilidad de rutas alternativas antes de juzgarlas. Si la descripción de un atajo es ambigua, pedir una comprobación breve; no confundir estilo con funcionamiento. Los atajos de dos letras van en secuencia.

## Lección 3 · trazo-anotar · «Leer y dejar una glosa» (`id: trazo-anotar`)

- **Objetivo observable:** distinguir anotación privada de contexto compartido y
  explicar la elección según la ayuda que se busca.
- **Enunciado:** «Dejá una anotación en un fragmento que te interese. ¿Qué conservarías
  privado y qué compartirías para que el tutor pueda ayudarte?»
- **Rúbrica (2 criterios):** (1) distinguir anotación privada de contexto compartido;
  (2) explicar la elección según la ayuda que se busca.
- **Consistencia:** coherente.
- **Respuesta mínima [AUTORÍA]:** «Conservaría privada la nota personal (duda o
  fragmento que no quiero exponer) y compartiría la duda con su fragmento si necesito
  que el tutor me ayude.»
- **Fuente local exacta:** `courses/tutorial.json` → `lessons[2].blocks[0].text`
  (`trazo-anotar-b1`), `tutor_context.py::defaults` y [contexto del tutor](contexto-tutor.md). La inclusión explícita puede compartir material privado; privado no significa imposible de enviar.
- **Riesgos:** aceptar paráfrasis breve y la decisión de no compartir material si distingue privacidad y contexto y explica su elección. No exigir revelaciones personales. No inferir dominio a partir de haber compartido algo o recibido una síntesis del tutor; evaluar cada criterio con evidencia propia.

## Lección 4 · trazo-conversar · «Conversar y continuar» (`id: trazo-conversar`)

- **Objetivo observable:** incluir la duda y su contexto/fragmento, y considerar la
  selección de datos compartidos y la conservación del historial.
- **Enunciado:** «Imaginá que querés retomar una duda mañana con un agente. ¿Qué
  guardarías y qué revisarías antes de compartir el pliego?»
- **Rúbrica (2 criterios):** (1) incluir la duda y su contexto o fragmento de origen;
  (2) considerar la selección de datos compartidos y la conservación del historial.
- **Consistencia:** coherente.
- **Respuesta mínima [AUTORÍA]:** «Guardaría la duda con su fragmento o contexto;
  antes de compartir revisaría qué material se envía (excluir lo privado) y que el
  historial quede conservado en el pliego.»
- **Fuente local exacta:** `courses/tutorial.json` → `lessons[3].blocks[0].text`
  (`trazo-conversar-b1`) y `lessons[3].blocks[1].text` (`trazo-conversar-b2`), contrastados con `llm_providers.py::save_credential`, [contexto del tutor](contexto-tutor.md) y `web/app.js::renderStudy` (encargo de continuación).
- **Riesgos:** aceptar respuestas breves. Contradicción a penalizar: decir que el
  respaldo sincroniza solo entre dispositivos (el texto dice que el respaldo es copia y
  no sincroniza automáticamente). No penalizar estudiar sin modelo conectado (consulta
  opcional según el texto).

## Observaciones transversales / uncertain

- **Video de lección 1** (`youtube`, `videoId cAqEVoiqudI`, «Glosa en movimiento»):
  contenido y titularidad **no inspeccionados** (`uncertain`). El encargo prohíbe
  ampliar la inspección; queda pendiente de confirmación en release (titularidad/permiso).
- **«Las respuestas de las actividades requieren guardarse para entrar al historial»**
  (`trazo-anotar-b2`): DeepSeek lo dejó como `uncertain` por evidencia limitada. El coordinador comprobó después `web/app.js`, `form.saveAnswer`, que registra el evento `answer`; el recorrido de estudio también ejercita el guardado. Esto verifica persistencia, no comprensión.
- **Cambios y límites:** DeepSeek no modificó el tutorial. El coordinador corrigió previamente la persistencia de claves y las garantías sobre el video, y después precisó el contexto del atajo `/`. Se conservan IDs, actividades y rúbricas en la versión 1.0.2. Las cuatro actividades son abiertas: no hay claves posicionales ni necesidad de generar una permutación.
- No se evaluaron respuestas reales ni se acreditó dominio. Se deben aceptar respuestas breves y paráfrasis, citar evidencia real por criterio y usar `uncertain` ante ambigüedad. Una revisión asistida y los recorridos simulados no acreditan la calidad de un tutor real.

## Confirmación del video · 2026-10-15

La persona responsable confirmó que hizo el video enlazado en el tutorial y
autorizó continuar con la release. Se cierra el pendiente de autoría y permiso
del video. Esta confirmación no se presenta como una inspección completa del
contenido ni como una auditoría de accesibilidad. No se modificaron los IDs,
las actividades ni las rúbricas del tutorial.
