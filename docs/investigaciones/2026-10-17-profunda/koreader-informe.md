# Informe · Evidencia REA **funcional** sobre KOReader v2026.07.1 (distribución oficial) para Glosa

Autor: agente OpenCode (modelo actual, sin delegar). Fecha: 2026-10-17.
Salida exclusiva: `/tmp/glosa-deep-20261017/koreader/`.
Target: `/tmp/glosa-koreader-research/koreader-v2026.07.1-x86_64/lib/koreader/` (solo lectura).

Este informe **profundiza** el trabajo previo (`/tmp/glosa-koreader-research/informe-deepseek.md`), que
había usado REA únicamente para identidad/ELF. Aquí se aporta **evidencia REA funcional** obtenida por
**replay de módulo** con `capture_process`, y se separa de forma explícita:
**[REA]** observado ejecutando código distribuido bajo REA; **[OTRA]** observado con otras herramientas
(lectura estática del corpus Lua); **[INF]** inferencia; **[PROP]** propuesta.

---

## 0. Alcance real: qué es esta evidencia y qué no

- **Es**: ejecución real de **5 funciones de 5 módulos Lua distribuidos** (no reimplementadas por mí),
  cargadas con `loadfile()` desde el árbol de KOReader y llamadas con entradas controladas, bajo
  `rea capture-process` (que captura el PTY, el exit code, la huella del ejecutable y las limitaciones).
- **No es** el runtime completo de KOReader: **no** se abrió la GUI, **no** se abrió ningún documento,
  **no** se usó el sqlite real (`lua-ljsqlite3` está stubbeado), **no** se tocó `HOME` real, **no** se
  cargó ningún módulo de dispositivo/red. Por eso **no** debe leerse como análisis de toda la app.
- **No sustituí** ninguna función por mi propia versión: el harness llama al símbolo real
  (`VocabularyBuilder:gotOrForgot`, `ReadTimer:remainingTime`, `prepareBookContent`, …).
- La arquitectura Lua de KOReader usa directorios con punto (`vocabbuilder.koplugin`); por eso el
  harness usa `loadfile(ruta_absoluta)()` en vez de `require`, preservando el archivo tal cual.

### Stubs explícitos por harness (mínimos; lo demás es código real)

| Harness | Módulo real ejecutado | Stubs aportados (NO son código real) |
|---|---|---|
| H1 | `plugins/vocabbuilder.koplugin/db.lua` → `gotOrForgot` | `datastorage`, `device`, `lua-ljsqlite3/init` (conn falsa, `rowexec`→`"20240905"`), `luadata`, `logger` |
| H2 | `plugins/readtimer.koplugin/main.lua` → `remaining`, `remainingTime` | widgets UI, `uimanager`, `logger`, `datetime`, **`ui/time` (reloj fijo `now()` y `to_s(x)=x`)**, `gettext`, `ffi/util` |
| H3 | `plugins/exporter.koplugin/template/md.lua` → `prepareBookContent`, `formatters` | `gettext`, `ffi/util.template` (sustitución `%N`) |
| H4 | `frontend/readhistory.lua` → `addItem`, `_reduce`, `getPreviousFile`, `getIndexByTime` | `datastorage`, `docsettings`, `datetime`, `dump`, `ffi/util` (`realpath`), `util.writeToFile`, `libs/libkoreader-lfs` (ficheros simulados), `gettext`, `G_reader_settings` |
| H5 | `frontend/apps/reader/modules/readersearch.lua` → `onShowFindAllResults` | widgets (`Menu`, `TextBoxWidget`, `InfoMessage`, `Notification`…), `UIManager`, `Device.screen`, `G_defaults`, `gettext`, `ffi/util`; **`ui.document` y `ui.annotation` simulados** |

Los stubs se documentan para que nadie los confunda con comportamiento nativo. En H5, la parte
probada es el **ensamblado de contexto de resultados**, no la extracción nativa de texto del documento
(que vive en el motor de documento, no en Lua).

---

## 1. Manifiesto de capturas REA

El ejecutable capturado en las 5 es el **LuaJIT empaquetado**, sha256:
`d45e2e20df501f0aabc2eb55c5e6138090d48bae423d4de87ac3df113e8eee3c`.
`frame` = fotograma de terminal con el stdout del harness. Todas terminan con `exit code 0`.

| Cap. | Módulo | Función | Evidencia REA (id) | stdout |
|---|---|---|---|---|
| s1 | `plugins/vocabbuilder.koplugin/db.lua` | `gotOrForgot` | `ev_a39543fc74012390378482ed35d302c3fca58d1cb364a2ae11992398233a4a90` | `out/s1-h1_vocab.stdout.txt` |
| s2 | `plugins/readtimer.koplugin/main.lua` | `remaining`/`remainingTime` | `ev_a6b04dfb3f4fc71608088072573849159793465f047669ca30bba74c14baa8d4` | `out/s2-h2_readtimer.stdout.txt` |
| s3 | `plugins/exporter.koplugin/template/md.lua` | `prepareBookContent` | `ev_1a30a22265d8c7650c001923c769bb9f8f1e6cb58552ac3f2c70d2005b09d2af` | `out/s3-h3_md.stdout.txt` |
| s4 | `frontend/readhistory.lua` | `addItem`/`_reduce`/`getPreviousFile` | `ev_9261afe5a0f397756071b9165d92a764f280547997d9b93240682c444222677e` | `out/s4-h4_readhistory.stdout.txt` |
| s5 | `frontend/apps/reader/modules/readersearch.lua` | `onShowFindAllResults` | `ev_063cb20c62a4e8ea739624b628738f7bd30e96573a0c3671a3d78f0bf1fcd64a` | `out/s5-h5_readersearch.stdout.txt` |

Cada captura conserva además `manifest.full_scenario_sha256` y el JSON completo de Evidence
(`out/rea-sN.json`) con sus `limitations`/`residual_unknowns` (REA declara que observa el árbol de
procesos por muestreo, el entorno heredado como desconocido y la red como no observada).

Hashes de los 5 módulos ejecutados: `evidencia/01-modulos-ejecutados.sha256.tsv`
(p. ej. `db.lua` = `b3574904e0d2…` 527 líneas; `readtimer/main.lua` = `10c617eba473…` 581 líneas;
`template/md.lua` = `ce29981714d8…` 70 líneas; `readhistory.lua` = `b6da914f0b49…` 375 líneas;
`readersearch.lua` = `622c9660df5a…` 985 líneas).

---

## 2. Hallazgos funcionales con evidencia REA (5 funciones)

En cada caso: **expectativa previa** (derivada de leer el módulo antes de ejecutar) y **resultado real
capturado** (no reimplementado). Esto cumple el requisito "no capturar solo stdout sin expectativas".

### F1 · Cola de repaso espaciado `VocabularyBuilder:gotOrForgot` [REA]

- **Rango**: `plugins/vocabbuilder.koplugin/db.lua:219-253`. **Evidencia**: s1.
- **Expectativa previa** (de leer la escalera): con `isGot=true`, `streak_count` crece 1 y
  `due_time - review_time` sigue `0→5 min, 1→30 min, 2→12 h, 3→24 h, 4→48 h, 5→96 h, 6→7 d, 7→15 d,
  n≥8→30 d·2^(min(n-8,6))`; con `isGot=false`, `streak_count→0`, `review_count→max(n-1,0)` y
  `due_time=+5 min`.
- **Resultado real** (stdout s1, deltas exactos en segundos):
  - `step=1 delta=1800` (30 min), `step=2 43200` (12 h), `step=3 86400` (24 h), `step=4 172800` (48 h),
    `step=5 345600` (96 h), `step=6 604800` (7 d), `step=7 1296000` (15 d), `step=8 2592000` (30 d),
    `step=9 5184000` (60 d) … `step=14 165888000` y `step=15 165888000` (**se topa** en 30 d·2⁶ = 1920 d).
  - `FORGOT_AFTER_STREAK`: `streak=0 review=14 delta=300`; `FORGOT_FRESH`: `review=0 delta=300`;
    `FORGOT_PARTIAL review_before=2 review_after=1`.
- **Hallazgo fino (no obvio en lectura rápida)**: el primer acierto de una palabra **fresca cae en la
  fila de 30 min, no en la de 5 min**; la fila de **5 min solo aparece tras un olvido** (`target_count==0`).
  Además el tope de intervalo es **fijo a partir de la racha 14**, no crecimiento indefinido.
- **Utilidad para Glosa**: es una receta determinista y testeable para convertir el registro pasivo de
  errores (`web/study-tools.js:269 logPartialError`) en una **cola de repaso con fechas**, sin acoplar
  ninguna evaluación.

### F2 · Temporizador: `ReadTimer:remaining` / `remainingTime` [REA]

- **Rango**: `plugins/readtimer.koplugin/main.lua:181` y `:196`. **Evidencia**: s2.
- **Expectativa previa**: `remaining()` = segundos enteros restantes o `math.huge` si no hay timer;
  `remainingTime(round)` descompone en H/M/S, con `round<0` resta 59 s, `round==0` suma 30 s,
  `round>0` suma 59 s **antes** de truncar a minutos.
- **Resultado real** (stdout s2):
  - `3661 → H=1 M=1 S=1`; `round0 → 1,1,0`; `rounddown → 1,0,0`; `roundup → 1,2,0`.
  - `59 → 0,0,59`; `3600 → 1,0,0`; `3601 roundup → 1,1,0`.
  - `remaining=inf` y `remainingTime` sin valores cuando `scheduled()==false` (timer = 0).
- **Límite declarado**: `ui/time` está stubbeado (reloj fijo). La **descomposición/redondeo** es
  código real; el reloj subyacente del dispositivo no se probó.
- **Utilidad para Glosa**: base para un **temporizador de simulacro** que solo mide ritmo y **nunca**
  cambia el veredicto de una actividad.

### F3 · Exportación Markdown: `prepareBookContent` [REA]

- **Rango**: `plugins/exporter.koplugin/template/md.lua:39-66`, formatos en `:4-37`. **Evidencia**: s3.
- **Expectativa previa**: `# título`, autor con `\n`→`, `, agrupación por capítulo (`## `) solo al
  cambiar de capítulo, línea `### Page N @ <fecha>`, texto con formato según `formatting_options[entry.drawer]`
  (`bold=**%s**`, `highlight==%s==`, `none=%s`), nota al pie con `\n---\n`, y backlink
  `[View in book](<file://…?pos=…>)` si `export_backlinks`.
- **Resultado real** (stdout s3): las tres entradas se emitieron exactamente así; el autor
  `"Autor Uno\nAutor Dos"` → `Autor Uno, Autor Dos`; capítulo 1 agrupado una sola vez; `**Concepto clave**`,
  `==Otra idea==`, `Sin estilo`; con `export_backlinks=true` apareció
  `[View in book](<file:///books/anatomia.pdf?pos=/body/xp1>)` (los `pn_xp` ausentes → `pos=nil`, dato honesto).
- **Utilidad para Glosa**: plantilla concreta para una **hoja de repaso Markdown por materia/parcial**
  reusando datos que Glosa ya guarda.

### F4 · Historial de lectura: `addItem` / `_reduce` / `getPreviousFile` [REA]

- **Rango**: `frontend/readhistory.lua:313` (`addItem`), `:81` (`_reduce`), `:160` (`getPreviousFile`),
  `:50` (`getIndexByTime`). **Evidencia**: s4.
- **Expectativa previa**: alta por recencia; reabrir un libro ya presente lo mueve al frente; el
  tamaño se recorta a `history_size`; `getPreviousFile` salta el actual y los borrados.
- **Resultado real** (stdout s4, `history_size=3`): tras añadir a,b,c,a → `ORDER=1:a 2:c 3:b`
  (a al frente). Un fichero inexistente `d.epub` **se añade** pero queda `select_enabled=false D_DIM=true`
  (no se descarta si no trae timestamp). Tras más inserciones y el tope: `ORDER2=1:c 2:b 3:d`;
  `PREV_OF_A=/books/c.epub`.
- **Hallazgo fino**: `addItem` **no rechaza** un archivo ausente cuando no se pasa timestamp; lo deja
  `dim` hasta que el historial se limpia (`clearMissing`). Es una distinción útil para "seguir donde dejé".
- **Utilidad para Glosa**: modelo de "última posición" con degradación explícita (aviso), sin abrir una
  ruta inexistente.

### F5 · Búsqueda: `ReaderSearch:onShowFindAllResults` (ensamblado de contexto) [REA]

- **Rango**: `frontend/apps/reader/modules/readersearch.lua:708-760`. **Evidencia**: s5.
- **Expectativa previa**: por cada hit construye `text = [HEADER] prev_text + (espacio si no termina en
  espacio) + [BOLD_START] prefijo + coincidencia + sufijo [BOLD_END] + (espacio si `next_text` no empieza
  con espacio/puntuación) + next_text`; `mandatory` = referencia de página.
- **Resultado real** (stdout s5):
  - `idx=1 text="<H>texto previo <B>claves</B> resto"` (prev ya termina en espacio → sin espacio extra).
  - `idx=2 text="<H>sin espacio <B>clave</B>. Fin"` (prev sin espacio → se agrega uno; `next` empieza en `.`
    → **no** se agrega otro).
  - `idx=3 text="<H><B>clave</B>"` (sin contextos).
  - `mandatory=p42/p77/p120` vía referencia de página simulada.
- **Límite declarado**: se stubbean `ui.document` (extracción nativa) y `ui.annotation` (sidecar); lo
  probado es el **formato/presentación de cada resultado**, que es lo trasladable a Glosa.

---

## 3. Otras observaciones (herramientas normales, NO REA) [OTRA]

Lectura estática del corpus Lua distribuido (675 archivos) y del repo Glosa. Sirven para el inventario,
**no** cuentan como evidencia REA funcional:

- Agenda/orden por vencimiento: `db.lua:35-49` (`selectCount`) y `:150-167` (`_select_items`,
  `ORDER BY due_time`, marca `is_dim`).
- Captura de contexto de vocabulario: `db.lua` esquema `prev_context/next_context/highlight`;
  `plugins/vocabbuilder.koplugin/main.lua` inserción.
- Límite de resultados de búsqueda: `readersearch.lua:61` (`findall_max_hits=5000`) y memoria del
  último término (`:253-254`).
- Anotaciones/anclas y sidecar: `frontend/apps/reader/modules/readerannotation.lua:255-280`.
- Mapa del libro: `readerpagemap.lua:183 updateVisibleLabels`, `:258 onShowPageList`; mapa sintético en
  el motor de documento (`buildSyntheticPageMap`, fuera de Lua analizada aquí → **desconocido**).
- Estadísticas: `statistics.koplugin/main.lua` (totales por libro/período; clamp de duración de página
  `diff_time<=max_sec ? diff_time : avg_time`, líneas ~600-663).
- Diccionario e historial de búsquedas: `readerdictionary.lua:41,177-178`.
- Glosa (estado real, confirmado en repo): `web/study-tools.js:25 ERROR_TYPES`, `:43 STUDY_FIELDS`,
  `:269 logPartialError`, `:287 filterNotes`; `library.py:32 study_markdown`, `:284 STUDY_FIELDS`,
  `:288 validate_study`; `web/app.js:62 statusLabel`, `:63` kinds (`assessment`, `study_time`, `visit`);
  `web/plan.js:38-52` (recomendación/Plan, Parciales); búsqueda en Notas (`web/notes.js` variable
  `query`, input `#class-note-search`); anclas `#note=ID` en `web/app.js:188-226`.

---

## 4. Incógnitas honestas (lo que NO pude analizar)

- **Runtime completo de KOReader**: no ejecutado. Comportamiento real de la GUI, del motor de documento
  (extracción de texto, `buildSyntheticPageMap`) y de `sdcv`/diccionarios: **desconocido**.
- **Acceso a sqlite real**: no se ejecutó `lua-ljsqlite3` (stubbeado). La corrección de las consultas SQL
  (`ORDER BY due_time`, `INSERT … ON CONFLICT`) es lectura estática, no ejecución.
- **Funciones nativas**: no se usó Ghidra (Ghidra/Hopper/IDA no configurados como proveedor REA; el
  alcance pedía priorizar Lua funcional). Los `.so` distribuidos no se decompilaron en esta pasada.
- **Módulos UI pesados** (estadísticas con DB, mapa de páginas con widgets, anotaciones con sidecar):
  solo lectura estática; marcados `origen=otra` o `desconocido` en el inventario.
- Sobre s1: REA reporta `settlement=alive_at_deadline` aunque `exit code 0`; se registra tal cual, no
  afecta a la salida capturada.

---

## 5. Propuestas priorizadas para Glosa [PROP]

Ninguna crea eventos `assessment` ni cambia estados de lección (`docs/evaluacion-rigurosa.md:19`,
`docs/herramientas-estudio.md:104-113`). Los conceptos nuevos se **enlazan dentro de las lecciones**
(`[SI](#note=ID)`, `docs/mcp-autor.md`), **no** en un glosario separado.

1. **[PROP] Cola de repaso con fechas derivada de F1** (prioridad alta). Campos `study.reviewDue`/
   `reviewStep`, reloj inyectable, lista "para repasar hoy" reusando `filterNotes`. Estado Glosa:
   **parcial** (errores sí, calendario no). Aceptación: con reloj fijo y errores de fechas conocidas, la
   cola es reproducible y no genera `assessment`.
2. **[PROP] Temporizador de simulacro derivado de F2** (prioridad media). Mide ritmo; jamás acredita.
3. **[PROP] Hoja de repaso Markdown derivada de F3** (prioridad media). Un `.md` por materia/parcial.
4. **[PROP] "Continuar donde dejé" derivado de F4** (prioridad media). Apunte+página+lección con aviso
   si el documento no existe.
5. **[PROP] Búsqueda con contexto y salto derivada de F5** (prioridad media-alta). Fragmento + resaltado
   + salto, agrupando apunte/lección/ejercicio; reusa `NoteMarkdown.render` y navegación existente.

Detalle de adaptación, riesgo y criterio de aceptación por funcionalidad en `inventario.json`.

---

## 6. Entregables

- `informe.md` (este archivo).
- `inventario.json` (20 funcionalidades; campos pedidos).
- `harness/*.lua` (5 harness de replay), `scenarios/*.json` (escenarios de `capture_process`).
- `out/rea-s{1..5}.json` (Evidence REA completa) y `out/s*-*.stdout.txt` (stdout capturado).
- `evidencia/00-luajit.sha256`, `01-modulos-ejecutados.sha256.tsv`,
  `02-rea-capturas-meta.json`, `03-indice.txt`.
