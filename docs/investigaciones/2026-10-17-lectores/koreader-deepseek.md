> Informe original de DeepSeek; ver [síntesis y revisión](README.md) para correcciones y prioridades finales. Las rutas de evidencia del agente corresponden a `/tmp/glosa-koreader-research`.

# Informe · Propuestas para mejorar Glosa a partir de KOReader v2026.07.1

Autor del informe: DeepSeek (agente en la sesión de OpenCode de `spogus`).
Fecha: 2026-10-17.
Encargo: investigación delegada, **sin implementar cambios**. Salida en `/tmp/glosa-koreader-research/`.

Este informe analiza la **distribución oficial KOReader v2026.07.1 (linux-x86_64)** y propone
mejoras concretas para Glosa, cuyo fin es **preparar parciales** (no "terminar libros por
cantidad"). Se separa siempre **nuevo** de **mejorar lo existente**, con rutas y líneas.

---

## 0. Resumen ejecutivo

- El paquete objetivo se verificó por integridad: tamaño y `sha256` reales coinciden con
  `release.json` (sección 1).
- REA se usó realmente sobre el artefacto distribuido. **REA no admite `.tar.xz`** como archivo
  contenedor y sus proveedores de análisis profundo (Ghidra/Hopper/IDA/pwntools) no están
  configurados en este host. Con REA **sí** se pudo confirmar identidad, formato y arquitectura de
  binarios ELF distribuidos (`luajit`, `libkoreader-cre.so`, `libsqlite3.so`, `libwrap-mupdf.so`).
  El detalle del bloqueo y qué se pudo comprobar por otras vías está en la sección 8.
- Toda la evidencia de comportamiento de KOReader es **estática** (lectura de recursos Lua
  distribuidos). **No se ejecutó KOReader**. Por lo tanto, lo observado es diseño de código
  distribuido, no comportamiento en ejecución.
- Se proponen **8 mejoras priorizadas** (sección 3), se identifican **3 prioridades** (sección 4) y
  **3 características de KOReader que NO conviene trasladar** (sección 5).

---

## 1. Identidad y verificación del artefacto (estático)

| Dato | Valor | Fuente |
|---|---|---|
| Release | KOReader v2026.07.1, publicado 2026-08-01T11:10:30Z | `release.json` |
| Asset | `koreader-linux-x86_64-v2026.07.1.tar.xz`, id 497834403 | `release.json` |
| Tamaño declarado / real | 30 144 476 bytes / 30 144 476 bytes | `release.json` / `stat` |
| Digest declarado | `sha256:299aadb28147a25e9432ced1214ea444a4184393b5ae97cf42402c8a61b1a1b0` | `release.json` |
| Digest real | `299aadb28147a25e9432ced1214ea444a4184393b5ae97cf42402c8a61b1a1b0` | `sha256sum` |
| `release.json` (metadatos) | `sha256:095c4ea8e457cd64f54259035e940537ed500648b8cb31ec1cbf4b84e63e22d3` | `sha256sum` |
| `git-rev` embebido en el paquete | `v2026.07.1` | `lib/koreader/git-rev` |

El paquete **ya estaba completo** al iniciar (no hubo que esperar descarga). Extraído a un
subdirectorio nuevo, sin ejecutar nada: `koreader-v2026.07.1-x86_64/` (94 MiB,
675 archivos `.lua` distribuidos).

**Identidades ELF obtenidas con REA (`open_binary`, formato `elf`, x86_64):**

| Binario | sha256 (REA) |
|---|---|
| `luajit` | `d45e2e20df501f0aabc2eb55c5e6138090d48bae423d4de87ac3df113e8eee3c` |
| `libs/libkoreader-cre.so` | `bafb2f8d235dada0dfa7772b468fb574ec2aa19d403a85f95261369bc63602ad` |
| `libs/libsqlite3.so.0` | `9341f59991c140a56a27c81bc8373db66b9db7820738b48ef7d4a78ff2b66a7f` |
| `libs/libwrap-mupdf.so` | `f86d6b6ebc1abbe8b36d3459e0fa1d6717c31e7cae7aaf2dc9fed31660591a25` |

**Archivos Lua clave analizados (sha256 / líneas):**

| Ruta (dentro de `lib/koreader/`) | sha256 (12) | Líneas |
|---|---|---|
| `frontend/readhistory.lua` | `b6da914f0b49` | 375 |
| `frontend/apps/reader/modules/readerhighlight.lua` | `a2e45bcaf245` | 2804 |
| `frontend/apps/reader/modules/readersearch.lua` | `622c9660df5a` | 985 |
| `frontend/apps/reader/modules/readerdictionary.lua` | `8ca93c7881b7` | 2030 |
| `frontend/apps/reader/modules/readerpagemap.lua` | `36a69f8bc5f4` | 666 |
| `frontend/apps/reader/modules/readerbookmark.lua` | `755c3f91901f` | 1693 |
| `frontend/apps/reader/modules/readerannotation.lua` | `bc33dc66bc63` | 563 |
| `plugins/statistics.koplugin/main.lua` | `da6db5e381bc` | 3240 |
| `plugins/vocabbuilder.koplugin/main.lua` | `a1435b39a8ec` | 2155 |
| `plugins/vocabbuilder.koplugin/db.lua` | `b3574904e0d2` | — |
| `plugins/readtimer.koplugin/main.lua` | `10c617eba473` | 581 |
| `plugins/exporter.koplugin/main.lua` | `179d0b5e0b6d` | 505 |
| `plugins/exporter.koplugin/target/markdown.lua` | `4f7480322075` | — |
| `frontend/docsettings.lua` | `2ac292560866` | 651 |

Los hashes completos y los manifiestos están en `evidencia/02-manifiesto-archivos-clave.tsv` y
`evidencia/03-manifiesto-lua-completo.sha256`.

---

## 2. Cómo leer este informe: estático vs runtime, ausente vs desconocido

- **Estático (lo que sí se observa):** estructura del código fuente Lua distribuido, nombres de
  funciones y constantes (p. ej., la escalera de intervalos de repaso en
  `plugins/vocabbuilder.koplugin/db.lua:219-253`). Esto describe el diseño empaquetado.
- **Runtime (desconocido):** el comportamiento real al abrir la app (orden efectivo de la cola de
  repaso, si `sdcv` encuentra diccionarios, latencia de búsqueda, persistencia real) **no** se
  observó. No se ejecutó KOReader ni se abrieron documentos.
- **Ausente dentro de un límite declarado:** por ejemplo, `grep -rli mastery --include=*.lua` sobre
  los 675 `.lua` dio **0** coincidencias. Esto significa "ausente en este corpus para esa palabra",
  **no** prueba de ausencia global del concepto ni de equivalentes.
- **Ausente vs desconocido:** cuando no se pudo inspeccionar algo (p. ej., el interior de un
  binario nativo por falta de proveedor), se marca **desconocido**, no "ausente".

---

## 3. Ocho propuestas priorizadas

Convención: **[MEJORA]** = se apoya en algo que Glosa ya tiene; **[NUEVO]** = capacidad que hoy no
existe. Cada propuesta cita la **característica comprobada** de KOReader con evidencia
localizable, el **estado real de Glosa**, la **interacción del estudiante**, la **adaptación
mínima**, el **beneficio esperado como hipótesis**, la **dificultad/riesgo** y el **criterio de
aceptación**.

---

### P1 · [MEJORA] Cola de repaso espaciado sobre errores propios y fichas

- **Característica comprobada (KOReader, estático):** el plugin Vocabulario define una **escalera
  determinista de intervalos** según aciertos consecutivos. Evidencia:
  `plugins/vocabbuilder.koplugin/db.lua` líneas **219-253** (`due_time` = +5 min, +30 min, +12 h,
  +24 h, +48 h, +96 h, +7 d, +15 d y luego `30 d * 2^(n-8)`), con `streak_count`/`review_count` y
  botones "lo sabía / lo olvidé" (`plugins/vocabbuilder.koplugin/main.lua`, `onGotIt` ~1124,
  `onForgot` ~1135). Ficha: `db.lua` sha256 `b3574904e0d2…`, `main.lua` sha256 `a1435b39a8ec…`.
- **Estado real de Glosa:** existe un **registro de errores de parcial** por apunte
  (`web/study-tools.js:269` `logPartialError`, tipos en `:25`, plantilla de ficha en `:26`) y una
  propiedad `needsPractice` (`web/study-tools.js:43`), validados y guardados dentro de la nota
  (`library.py:284` `STUDY_FIELDS`, `:288` `validate_study`). **No hay** ningún cálculo de próxima
  fecha de repaso: el error es un registro pasivo.
- **Interacción del estudiante:** al registrar un error o completar una ficha, el sistema propone
  la próxima fecha de repaso; en Notas y en **Plan → Parciales** aparece una lista "Para repasar
  hoy" con elementos vencidos.
- **Adaptación mínima:** agregar dos campos opcionales al esquema `study`
  (`reviewDue`, `reviewStep`) en `library.py` y `web/study-tools.js`, calcular el intervalo en una
  función pura (determinista, con reloj inyectable) y mostrar la lista reutilizando
  `filterNotes`/`renderNoteListBadges` existentes.
- **Beneficio esperado (hipótesis):** convertir un registro pasivo de errores en **práctica de
  recuperación** repartida antes del parcial. Es una hipótesis pedagógica razonable, **no** una
  promesa de aprendizaje.
- **Dificultad / riesgo:** media. Riesgo principal: gamificación o falsa sensación de dominio
  ("lo marqué y ya está"). Mitigación: **la cola nunca cambia el estado de la lección ni crea
  eventos `assessment`**; se rotula como material de repaso (coherente con
  `docs/herramientas-estudio.md:112`).
- **Criterio de aceptación:** con un reloj fijo y N errores de fechas conocidas, la lista "para
  repasar hoy" es idéntica y ordenada de forma reproducible; persistir y recargar no altera la
  cola; ninguna acción de repaso produce un evento `assessment` ni marca `independent`; test de
  navegador con base temporal (patrón de `tests/browser_study_tools.cjs`).

---

### P2 · [MEJORA] Búsqueda con contexto y salto dentro de apuntes y lecciones

- **Característica comprobada (KOReader, estático):** búsqueda de texto completo con **lista de
  resultados**, salto y resaltado. `frontend/apps/reader/modules/readersearch.lua`:
  `findAllText` (línea 680), `onShowFindAllResults` (708), `showAllResultsMenuDialog` (791),
  `gotoResultsItem` (873), tope `findall_max_hits = 5000` (línea 61) y memoria del último término
  por documento (`fulltext_search_last_search_text`, líneas 253-254). Ficha sha256
  `622c9660df5a…`.
- **Estado real de Glosa:** **ya existe** una búsqueda en la barra lateral de Notas que filtra
  por **título + contenido + `pageNotes`**: `web/notes.js:320`
  (`${n.title} ${n.content} ${JSON.stringify(n.pageNotes||{})}…includes(query)`), con input en
  `web/notes.js:362`. Lo que **no** existe: fragmentos de contexto, resaltado del término, salto a
  la posición exacta, y búsqueda en el **texto de lecciones/ejercicios** (hoy `lesson-search`
  filtra solo por título de lección: `web/app.js:618`).
- **Interacción del estudiante:** escribe un término y ve resultados **agrupados por apunte,
  lección y ejercicio**, con un fragmento alrededor de la coincidencia; al hacer clic abre la nota o
  la lección y posiciona cerca del fragmento, sin perder el borrador.
- **Adaptación mínima:** construir un índice en memoria desde `state.library.notes` y
  `state.courses` ya presentes; reutilizar `NoteMarkdown.render` para el contexto, `ClassNotes.select`
  y la navegación de lección existentes. No requiere backend nuevo.
- **Beneficio esperado (hipótesis):** encontrar rápido el fragmento exacto durante el repaso
  reduce la fricción de la recuperación activa.
- **Dificultad / riesgo:** baja-media. Riesgo: rendimiento con muchas notas y falsos positivos sin
  resaltado claro. Mitigación: límite de resultados y coincidencia insensible a mayúsculas/acentos.
- **Criterio de aceptación:** para un término presente en una nota y en una lección, la búsqueda
  devuelve ambos con fragmento; el clic navega y conserva el borrador (verificable con test
  reproducible); no se indexa ni se envía nada fuera del navegador.

---

### P3 · [NUEVO] Temporizador de simulacro con separación explícita entre "avanzar por tiempo" y "acreditar"

- **Característica comprobada (KOReader, estático):** temporizador de lectura con inicio, tiempo
  restante y alarma. `plugins/readtimer.koplugin/main.lua`: `onStartTimer` (495), `remaining`
  (181), `remainingTime` (196), `onShowAlarm` (423). Ficha sha256 `10c617eba473…`.
- **Estado real de Glosa:** existen **simulacros** producidos por el autor de pliegos
  (`docs/mcp-autor.md:28,110-111`; `author_mcp.py:36`) y se renderizan en la lección
  (`web/app.js:151` `renderSimulation`). **No** hay tiempo por pregunta. La regla del proyecto ya
  exige **separar avanzar por falta de tiempo de acreditar aprendizaje**
  (`docs/evaluacion-rigurosa.md:19`).
- **Interacción del estudiante:** durante un simulacro ve un tiempo por ejercicio y uno total; al
  agotarse el tiempo, el ejercicio se marca **"no terminado por tiempo"**, que **no** equivale a
  incorrecto.
- **Adaptación mínima:** widget de temporizador opcional que lee los minutos de la lección
  (`l.minutes`, ya usado en `web/app.js:132` y `web/plan.js:53`), guarda marcas de tiempo en el
  `data` del evento de respuesta y **no** toca la lógica de evaluación (`assessment_rules.py`).
- **Beneficio esperado (hipótesis):** practicar el ritmo del parcial y hacer explícita la
  distinción tiempo/dominio que la propia regla pide.
- **Dificultad / riesgo:** media. Riesgo alto de interpretarse como evidencia de aprendizaje.
  Mitigación: la UI declara "el tiempo no acredita dominio"; al recargar la pestaña no se duplican
  minutos (advertencia de `docs/propuesta-evolucion.md` §3 sobre temporizadores en segundo plano).
- **Criterio de aceptación:** pausar y recargar no duplica el tiempo transcurrido; el veredicto de
  la evaluación es idéntico con y sin temporizador; la UI muestra el rótulo de no-evidencia.

---

### P4 · [MEJORA] Glosario local por materia alimentado por dudas y términos

- **Característica comprobada (KOReader, estático):** el diccionario guarda **historial de
  búsquedas** (`frontend/apps/reader/modules/readerdictionary.lua:41,177-178`
  `lookup_history.lua`), y el vocabulario captura **contexto** alrededor de la palabra
  (`prev_context`/`next_context`, `highlight`, `book_title`; inserción en
  `plugins/vocabbuilder.koplugin/main.lua:2118`). Fichas sha256 `8ca93c7881b7…` / `a1435b39a8ec…`.
- **Estado real de Glosa:** un "glosario" solo se menciona como nota enlazable
  (`docs/mcp-autor.md:141`, `[SI](#note=ID)`); no hay una vista consolidada de términos.
- **Interacción del estudiante:** al marcar una duda o un término, este se agrega a un apunte de
  glosario por materia con su definición propia y su fuente.
- **Adaptación mínima:** reutilizar la ficha de concepto (`CONCEPT_CARD_TEMPLATE`) y el patrón de
  enlace nativo `#note=ID`; sin diccionario externo obligatorio.
- **Beneficio esperado (hipótesis):** siglas y términos explicados evitan re-descubrir conceptos
  durante el repaso (la regla pide "explicá todas las siglas": `docs/mcp-autor.md:110`).
- **Dificultad / riesgo:** baja. Riesgo: duplicación de fichas; mitigación: una entrada por término
  normalizado.
- **Criterio de aceptación:** un término nuevo crea/actualiza una única entrada de glosario
  navegable desde la nota que lo originó; sin red y sin diccionarios externos.

---

### P5 · [MEJORA] "Seguir donde dejé" con apunte y página del PDF

- **Característica comprobada (KOReader, estático):** historial de lectura que registra el último
  libro y el anterior. `frontend/readhistory.lua`: `addItem` (313), `getPreviousFile` (160),
  `updateLastBookTime` (343), `_reduce` (81). Ficha sha256 `b6da914f0b49…`.
- **Estado real de Glosa:** existe el evento `visit` ("Lectura iniciada", `web/app.js:63`),
  `state.recommendations` y un botón de abrir recomendación en Plan (`web/plan.js:48`), y se
  recuerda página de PDF/zoom en Notas. Falta una acción única de **continuar** que combine apunte
  + página + lección.
- **Interacción del estudiante:** desde Plan o Notas, un botón "Continuar" reabre exactamente el
  apunte, la página del PDF y la posición de la lección donde quedó.
- **Adaptación mínima:** persistir un pequeño objeto de "última posición" (ya hay almacenamiento de
  borradores por nota) y exponerlo en la tarjeta de recomendación existente.
- **Beneficio esperado (hipótesis):** reduce el tiempo de reubicación al retomar el estudio.
- **Dificultad / riesgo:** baja. Riesgo: desincronización si se borra el documento; mitigación:
  degradar con aviso, sin inventar posición.
- **Criterio de aceptación:** tras cerrar y recargar, "Continuar" restaura apunte/página/lección;
  si el documento ya no existe, avisa y no abre nada incorrecto.

---

### P6 · [MEJORA] Mapa del temario con marcas de estado

- **Característica comprobada (KOReader, estático):** el "mapa del libro" muestra etiquetas de
  página visibles y una lista de páginas/etiquetas, incluyendo mapa sintético si el documento no
  trae uno. `frontend/apps/reader/modules/readerpagemap.lua`: `updateVisibleLabels` (183),
  `getPageMapVisiblePageLabels` (195), `onShowPageList` (258), `buildSyntheticPageMap` (70/76).
  Ficha sha256 `36a69f8bc5f4…`.
- **Estado real de Glosa:** los estados por lección existen y se usan en la barra lateral
  (`web/app.js:62` `statusLabel`, `:116` marcadores `independent/with_help/pending`), y `Plan`
  lista el recorrido con su estado (`web/plan.js:53`). No hay una vista **compacta tipo "mapa"**.
- **Interacción del estudiante:** una franja del temario donde cada lección es una marca coloreada
  por estado (`independent` / `with_help` / `pending` / sin explorar) con indicador de errores
  registrados; clic para abrir.
- **Adaptación mínima:** un componente visual que consuma `course().lessons` + `state.recommendations`
  + `study.errors`; sin datos nuevos.
- **Beneficio esperado (hipótesis):** ayuda a decidir **qué unidad no está comprobada** antes del
  parcial, en lugar de medir volumen leído.
- **Dificultad / riesgo:** baja. Riesgo: que el color se lea como nota otorgada; mitigación: leyenda
  con los mismos rótulos de `statusLabel` y aclaración de que no es calificación.
- **Criterio de aceptación:** cada lección aparece una vez con el color de su estado real; cambiar
  el estado (evento real) cambia el color tras recargar; sin estados inventados.

---

### P7 · [MEJORA] Esfuerzo registrado, rotulado como no-evidencia

- **Característica comprobada (KOReader, estático):** estadísticas de lectura por tiempo y páginas,
  con totales, por libro y por período. `plugins/statistics.koplugin/main.lua`: `getTotalStats`
  (2269), `getBookStat` (1677), `getCurrentStat` (1508), límites de duración de página
  (`Read page duration limits`, 1067/1091), calendario (`onShowTimeRange`, 1304). Ficha sha256
  `da6db5e381bc…`.
- **Estado real de Glosa:** se registran eventos `study_time` ("Tiempo de estudio",
  `web/app.js:63`) y `Plan` muestra minutos de disponibilidad aclarando que no es sesión
  programada (`web/plan.js:46`). No hay un panel que muestre el esfuerzo junto a las
  comprobaciones.
- **Interacción del estudiante:** un resumen "Minutos por materia · comprobaciones independientes vs
  con ayuda", con rótulo fijo de que el tiempo **no** acredita dominio.
- **Adaptación mínima:** agregar una vista que agregue eventos ya existentes (`study_time`,
  `assessment`, `feedback`); sin nueva captura.
- **Beneficio esperado (hipótesis):** permite ver dónde se invierte tiempo sin estudiar aún, y
  evita confundir esfuerzo con logro.
- **Dificultad / riesgo:** baja-media. Riesgo: **su mal uso** (leerlo como progreso). Mitigación: se
  contrasta explícitamente contra los estados `independent` y se declara no-evidencia
  (coherente con `README.md:30`, `docs/evaluacion-rigurosa.md:19`).
- **Criterio de aceptación:** las cifras se reconstruyen desde eventos; el panel nunca muestra el
  tiempo como dominio y no cambia ningún estado de lección.

---

### P8 · [NUEVO] Hoja de repaso Markdown por materia/parcial

- **Característica comprobada (KOReader, estático):** exportación/importación de anotaciones a
  `.annotations.lua` (`frontend/apps/reader/modules/readerannotation.lua:255-280`) y exportador a
  **Markdown**. `plugins/exporter.koplugin/main.lua:83` (`markdown = require("target/markdown")`) y
  `plugins/exporter.koplugin/target/markdown.lua:64-68,106`. Fichas sha256 `bc33dc66bc63…` /
  `179d0b5e0b6d…` / `4f7480322075…`.
- **Estado real de Glosa:** hay exportación de pliego ZIP y de notas/historial
  (`web/notes.js:364` abre `export-dialog`; `README.md:28`), y la nota admite metadata de estudio en
  su exportación Markdown (`library.py:32` `study_markdown`). Falta una hoja consolidada por
  parcial (resaltados + fichas + errores + dudas).
- **Interacción del estudiante:** genera un único `.md` por materia/parcial para imprimir o revisar
  fuera de la app.
- **Adaptación mínima:** una función de exportación que reúna datos ya existentes
  (`study.errors`, fichas en el cuerpo de la nota, `anchors` de PDF) respetando la exclusión de
  borradores solo-en-navegador (`README.md:28`).
- **Beneficio esperado (hipótesis):** material de repaso portátil y revisable sin la app.
- **Dificultad / riesgo:** baja. Riesgo de privacidad: es un archivo con datos personales;
  debe quedar claro y local (no se comparte automáticamente).
- **Criterio de aceptación:** la hoja contiene exactamente los errores/fichas/resaltados existentes,
  sin inventar secciones; se puede verificar por conteo contra el estado; no incluye borradores aún
  no guardados.

---

## 4. Las tres prioridades

1. **P1 · Repaso espaciado de errores y fichas.** Es el mayor apalancamiento para un parcial:
   convierte el registro de errores que **ya existe** en práctica de recuperación, y toca solo
   metadata propia sin afectar la puerta de evidencia. Respeta "no confundir esfuerzo con dominio".
2. **P2 · Búsqueda con contexto y salto.** Bajo costo (datos ya en memoria) y alto uso diario
   durante el repaso; mejora algo que **ya existe** de forma limitada.
3. **P3 · Temporizador de simulacro con separación tiempo/dominio.** Se alinea directamente con la
   regla de evaluación vigente y con el objetivo de preparar parciales con ritmo real.

Orden sugerido de implementación: P2 (rápido) → P1 (núcleo de repaso) → P3 (requiere cuidado de
estados y recarga).

---

## 5. Tres características que NO trasladaría

1. **Estadísticas de lectura (tiempo/páginas) como indicador de progreso o dominio**
   (`plugins/statistics.koplugin`). Contradice la regla de Glosa: el tiempo con la página visible
   es una medida aproximada, no prueba de atención ni de comprensión (`README.md:30`,
   `docs/evaluacion-rigurosa.md:19`, `docs/herramientas-estudio.md:112`). En P7 se toma solo la
   *presentación* de esfuerzo, **rotulada como no-evidencia** y subordinada a los estados reales.
2. **Gestión de biblioteca tipo estantería/cantidad:** portadas (`plugins/coverbrowser.koplugin`),
   Calibre (`plugins/calibre.koplugin`), OPDS (`plugins/opds.koplugin`), archivar/ordenar por
   "terminar libros". Glosa busca **dominio para parciales**, no volumen de libros terminados
   (encargo explícito). Añadiría superficie sin impacto en el objetivo.
3. **Sincronización remota de progreso/estadísticas entre dispositivos**
   (`plugins/kosync.koplugin`, evento `SyncBookStats` en `statistics.koplugin/main.lua:109`).
   Glosa se sirve en **loopback y Tailscale Serve privado**, sin cuentas (`README.md:24`);
   sincronizar introduce superficie de privacidad y no aporta a preparar un parcial.

(Otras no trasladables, mencionadas al pasar: mazos de vocabulario pensados para **idiomas
extranjeros** y descarga de diccionarios externos como requisito.)

---

## 6. Propiedades transversales de las propuestas

- Ninguna propuesta **crea eventos `assessment`** ni cambia el estado de una lección: el material
  de repaso es ayuda, coherente con `docs/herramientas-estudio.md:104-113` y
  `docs/modos-tutor.md:22-28`.
- Todas son **locales y deterministas** (sin azar, sin red, sin llamadas pagas), alineadas con
  `docs/modos-tutor.md:3-4` y `docs/evaluacion-rigurosa.md:10`.
- Todas respetan la **privacidad**: nada sale del equipo salvo exportación explícita del estudiante.
- P1 y P3 requieren **reloj inyectable** para poder testearse de forma reproducible.

---

## 7. Qué es nuevo y qué mejora lo existente (resumen)

| # | Tipo | Se apoya en (Glosa) |
|---|---|---|
| P1 | Mejora | `study.errors`, `needsPractice`, fichas, Plan Parciales |
| P2 | Mejora | búsqueda de Notas (`notes.js:320`), navegación de lección |
| P3 | Nuevo | render de simulacros, `l.minutes`, regla de evaluación |
| P4 | Mejora | ficha de concepto, enlaces `#note=ID`, dudas |
| P5 | Mejora | evento `visit`, `recommendations`, estado de página de PDF |
| P6 | Mejora | `statusLabel`, `course().lessons`, `study.errors` |
| P7 | Mejora | eventos `study_time`/`assessment`, minutos de Plan |
| P8 | Nuevo | exportación de notas/pliego, `study_markdown`, `anchors` |

---

## 8. Bloqueos reales y alcance de REA

**Lo que REA permitió comprobar (evidencia real):**
- `open_binary` sobre binarios ELF distribuidos devolvió **formato `elf`, arquitectura `x86_64` y
  sha256** de `luajit`, `libs/libkoreader-cre.so`, `libs/libsqlite3.so.0` y `libs/libwrap-mupdf.so`.
- `rea --version` = 6.4.0; `rea doctor` ejecutado (resumen en `evidencia/00-entorno-y-hashes.txt`).

**Bloqueo 1 — contenedor `.tar.xz` no soportado.** `open_binary` sobre el paquete devolvió
`target_unavailable` / `unsupported binary format`. REA 6.4.0 admite contenedores
`zip, ipa, apk, msix, appx, asar, dmg, pkg`; **no** `.tar.xz`. No se intentó engañar al detector
(p. ej. renombrando a `.zip`). `open_binary` sobre el directorio extraído también se rechaza
("this opening route requires a file or app bundle").

**Bloqueo 2 — proveedores de análisis profundo no configurados.** `binary_overview`,
`inspect_binary_layout` y `read_bytes` devolvieron `provider_unavailable`:
- Ghidra: `GHIDRA_INSTALL_DIR` no seteado.
- Hopper: `/opt/hopper/bin/Hopper` ausente.
- IDA: `REA_IDA_MCP_CONFIG` ausente.
- `pwntools-elf`: `REA_PWNTOOLS_PYTHON` ausente (requiere pwntools 4.15, pyelftools 0.33, Unicorn 2.1.2).

No se instaló ni configuró nada (fuera del alcance autorizado: "no setup global"). Por eso **no**
hay pseudocódigo ni inventario de funciones nativas.

**Qué se comprobó con otras herramientas (estático, sin ejecutar):**
- Integridad del paquete: `sha256` y tamaño reales contra `release.json` (coinciden).
- Extracción segura a un subdirectorio nuevo y lectura/grep de los **recursos Lua distribuidos**
  (675 archivos).
- Verificación local del estado de Glosa leyendo el repo fuente (herramienta normal, sin REA, según
  la indicación "REA solo para artefactos distribuidos").

**Límites declarados:**
- Todo es **estático**. No se ejecutó KOReader ni Glosa; el comportamiento en runtime es
  **desconocido**.
- Las búsquedas negativas (p. ej. `mastery` = 0) valen solo para ese término y ese corpus.
- El análisis de Glosa no modificó ni ejecutó nada del repo.

**Fuera de alcance respetado:** no se leyeron `~/Margen`, `<HOME>/Margen`, `.local-data`,
bases, fuentes, documentos ni configuraciones personales; no se leyeron logs/resultados de otros
agentes; no se delegó a otros modelos ni se activaron MCP pendientes; no se hizo ninguna compra ni
llamada paga.

---

## 9. Evidencia en disco

Directorio: `/tmp/glosa-koreader-research/`

| Archivo | Contenido |
|---|---|
| `informe-deepseek.md` | Este informe |
| `evidencia/00-entorno-y-hashes.txt` | Identidad del paquete, comandos REA y resultado de cada uno |
| `evidencia/02-manifiesto-archivos-clave.tsv` | sha256/líneas/bytes de los archivos Lua clave |
| `evidencia/03-manifiesto-lua-completo.sha256` | sha256 de los 675 `.lua` distribuidos |
| `evidencia/04-koreader-extracciones.txt` | Greps reproducibles con rutas y líneas (KOReader) |
| `evidencia/05-glosa-extracciones.txt` | Greps reproducibles con rutas y líneas (Glosa) |
| `koreader-v2026.07.1-x86_64/` | Árbol extraído (solo lectura) |
| `rea-evidence-bundle.json` | Bundle REA (0 registros: la identidad sin proveedor no se retiene) |

---

## 10. Conclusión

KOReader aporta piezas **concretas y verificables** para el problema de Glosa (repaso espaciado de
errores, búsqueda con contexto, temporizador de simulacro, mapa del temario, exportación), pero su
filosofía dominante —medir lectura por tiempo y cantidad de libros— es **contraria** al objetivo de
acreditar dominio para un parcial. La recomendación es **adaptar conceptos mínimos** sobre la
metadata de estudio que Glosa ya tiene, manteniendo intacta la separación entre ayuda, esfuerzo y
evidencia de dominio.
