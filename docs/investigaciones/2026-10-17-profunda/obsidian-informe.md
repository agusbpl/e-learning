# Obsidian → Glosa: hallazgos funcionales con REA (profundización)

Investigación de sólo lectura sobre el **target binario** de Obsidian. **No se
modificó código de Glosa**, ni bóvedas, ni datos reales, ni configuraciones
globales. Salida exclusiva: `/tmp/glosa-deep-20261017/obsidian/`.

- Modelo: **DeepSeek V4.1 Flash Free** (OpenCode). **Sin delegación** a otros
  modelos/proveedores ni APIs pagas. Sin navegación web.
- Fecha: 2026-10-17.
- Target: `/usr/lib/obsidian/obsidian.asar`
  (`SHA-256 146ef8470d8cbb4a6db209bdc19bf2bad13350444186c0fd93c31087b142b92f`),
  bundle renderer `app.js` extraído
  (`SHA-256 958ce57fe22f87fdf121546e46dfccd9c8ee971ce3fd8f801d60d4ece39a2df9`).
- Encargo: obtener **hallazgos funcionales verificables por REA** (trazas de
  características, análisis de funciones) en lugar de identidad/inventario, y
  separar evidencia REA / otras herramientas / inferencia / propuesta.

> Aclaración de alcance: esto **no** analiza toda la aplicación Obsidian. Analiza
> un **corpus derivado reducido** de 90 funciones reales extraídas por AST del
> bundle, declarado como tal. Cada afirmación funcional se ancla a una relación
> semántica o a una traza de REA con rango de bytes de origen. Lo no cubierto se
> enumera como incógnita (§6).

---

## 1. Metodología reproducible

Se siguió `reverse-engineer-anything/SKILL.md` (enrutar ASAR/Electron →
`analyze_javascript_application`, trabajar *summary-first*, reusar evidencia
previa, distinguir observación/inferencia/desconocido) y su
`references/javascript-applications.md`.

Como el análisis semántico del bundle completo ya había fallado por escala
(SIGTERM, `ev_666da7…`), **no se repitió** el bundle entero con más timeout: se
aplicó la vía recomendada para artefactos grandes, **corpus derivado reducido**.

### 1.1 Pasos

1. **Lectura previa** (reúso, no repetición): `informe-deepseek.md` y
   `/tmp/glosa-obsidian-research/evidence/*` (hashes, `app.js` extraído, header
   del ASAR, resultados REA previos).
2. **Extracción por AST** (`tools/extract_functions.mjs`, `@babel/parser` de la
   instalación de REA): se parseó `app.js` (0 errores recuperados), se
   recolectaron 15 442 funciones nombradas y se seleccionaron 90 por patrones
   **fuertes de nombre** en 8 categorías (preview/hover, navegación/historial,
   enlaces/resolución, búsqueda, outline, embeds, callouts, metadatos) con tope
   por categoría. Cada unidad conserva `ast_char_range`, `ast_byte_range`,
   `orig_slice_sha256` y la transformación aplicada (todas `wrap-export`).
3. **Verificación de procedencia:** los 90 fragmentos se re-leen desde
   `obsidian_app.js` en su rango de bytes y su SHA-256 coincide. **90/90 ok**.
4. **Análisis REA #1** (`analyze-javascript-application corpus`):
   `ev_87d26e1f9bf43cc1bbd70d9cefeeab65951eb808a887f49bf4ed92a3b789a3bc` —
   90 archivos parseados, **0 fallos**, 18 944 nodos AST, 94 findings,
   **13 037 relaciones semánticas**, 212 fingerprints.
5. **Análisis REA #2-5** (`trace-application-feature`, semilla `module`):
   4 trazas sobre el anterior Evidence (`ev_2f0661…`, `ev_92a9b9…`,
   `ev_278724…`, `ev_557076…`).
6. **Vista REA #6** (`inspect-analysis-view`, `source.kind=inline`): proyección
   del módulo `047_t.prototype.loadEmbed.js`
   (`ev_2a62d6db13b66dc06f389fee59f4dcceac34bab72d3cc44f440318fc25696f3f`,
   `parent_evidence_id = ev_87d26e1f…`, `complete-within-view`, 1/270).

Comandos (forma):

```
rea analyze-javascript-application corpus --format json
rea trace-application-feature evidence/trace-<n>-input.json --format json
rea inspect-analysis-view evidence/view-loadEmbed-input.json --format json
```

### 1.2 Qué es «corpus derivado reducido» y qué no

- **Es** código real de `app.js`: cada archivo del corpus es un fragmento
  verbatim, con rango y digest verificados contra el bundle original.
- **No es** la aplicación completa: el **contexto de módulo no se incluye**
  (las variables externas minificadas no se resuelven) y sólo entra 1 función por
  unidad. Por eso REA resuelve el análisis *intra-función* con alta fidelidad,
  pero las relaciones **entre** funciones del bundle quedan, en su mayoría,
  fuera del corpus (declarado en las limitaciones de REA: `coverage.partial`).

### 1.3 Herramientas usadas (separación de origen)

- **REA (núcleo del encargo):** `analyze-javascript-application`,
  `trace-application-feature`, y la lectura de sus Evidence JSON.
- **Otra (no-REA):** `@babel/parser` local para **aislar** funciones y
  preservar rangos; `sha256sum`/`node:crypto` para digests; lectura del repo de
  Glosa con herramientas normales; i18n `es.txt` e inventario del ASAR ya
  extraídos en la investigación previa.
- **Inferencia:** toda propuesta de adaptación y todo beneficio de estudio
  (marcados como hipótesis) — nunca se declara comportamiento en ejecución.

**Nada se observó en runtime.** No se arrancó Obsidian, no se abrió ninguna
bóveda, no hubo captura de proceso/Electron. Toda relación REA es **estática**
(`authority: ast-static-analysis` / `static-relationship-inference`).

---

## 2. Evidencia REA (IDs canónicos)

| Evidencia | Operación | Resultado |
|---|---|---|
| `ev_87d26e1f9bf43cc1bbd70d9cefeeab65951eb808a887f49bf4ed92a3b789a3bc` | `analyze_javascript_application` (corpus reducido) | 90/90 parseadas, 18 944 nodos AST, 13 037 relaciones, 212 fingerprints |
| `ev_2f06611ab5c75108619373f555d2762e7d0db94af0d47f41cd5e979864aaad7d` | `trace_application_feature` (módulo `loadEmbed`) | 2 semillas, 3 nodos, 2 aristas, 0 desconocidos, `paths` 0 |
| `ev_92a9b970950b93ed5ee104510033408c5c143b3b5ce712c839675fe7ce140a21` | `trace_application_feature` (módulo `updateSearch`) | idem, export `default` |
| `ev_278724314d1b54e7f642e094846db186de0c3f5637efd1de8f474f8f88d18e26` | `trace_application_feature` (módulo `startHover`) | idem |
| `ev_557076052e4cc16babbab7c2459728481777a0a01ca0f57a6dd1340cc1fb6e87` | `trace_application_feature` (módulo `findCurrentOutlineItem`) | idem |
| `ev_2a62d6db13b66dc06f389fee59f4dcceac34bab72d3cc44f440318fc25696f3f` | `inspect_analysis_view` (módulo `loadEmbed`) | `parent=ev_87d26e1f…`, `complete-within-view`, export `default`, commonjs, líneas 1–12 |
| `ev_666da72795dc1cd5730926fb3d660c498b45759f4917064530c93b5c01a9dceb` | `analyze_javascript_application` (obsidian.asar completo, previo) | parcial (SIGTERM en fase semántica) |
| `ev_59d450728ffd97f380c2653460c60b1f4b34d7abd0fe0eb85e9975121aa0d053` | `analyze` (app.asar, previo) | shell Electron, no renderer |

Esquema del grafo semántico del corpus (`ev_87d26e1f…`), útil para leer los
hallazgos:

- **Tipos de nodo:** expression 7097, call-site 1054, property-slot 683, binding
  607, function 212, module 90, return-site 267, parameter 208, literal 14,
  timer 3, promise 2.
- **Relaciones (`relation`):** aliases 7297, reads 2207, defines 1196, captures
  981, reads-property 873, writes 360, writes-property 51, argument-to-parameter
  26, calls 20, returns-to-call 19, **schedules-timer 3**, creates-promise 2,
  **cancels-timer 1**, detaches-task 1.
- **Cobertura:** `partial`, `truncated: true`; familias `call-flow`, `data-flow`,
  `object-flow` mayormente *unknown* fuera de las funciones analizadas (declarado
  por REA: «Graph coverage is incomplete; unavailable facts must not be read as
  absence»).

Los 4 traces resolvieron la semilla a **módulo + asset** (mismo `label`), y
devolvieron la arista de **contención** `artifact ⊃ asset ⊃ module` y la arista
**`exposes`** `default` (CommonJS) con rango `[línea 11, col 0–2097]` en
`047_t.prototype.loadEmbed.js`. `paths` terminales = 0 (el corpus no modela el
árbol de importaciones real; incógnita §6).

---

## 3. Hallazgos funcionales verificables por REA (profundización ≥ 5)

Cada fila liga una **función real de Obsidian** (rango en `app.js` + SHA-256 del
fragmento) con lo que REA **efectivamente observó** (relaciones semánticas /
trazas). Rangos en bytes de `app.js`; en el ASAR sumar 764 147.

### 3.1 `t.prototype.loadEmbed` — carga de embeds (F03)

- Rango `app.js` **[2432083, 2434163)**, sha `613817c9…59f9bf2`.
- REA observó (relaciones salientes de esta función):
  **`writes-property` → `label`, `height`, `width`** (3) y
  **`creates-promise` → `Promise.new`**; nodo literal `false`.
  El trace `ev_2f0661…` resolvió el módulo y su **export `default`**.
- **Lectura funcional (observada):** la carga de un embed **mide/etiqueta** el
  contenedor (alto, ancho, label) y **crea una promesa** — patrón coherente con
  cargar contenido incrustado de forma asíncrona antes de pintarlo.
- **Inferencia (declarada):** que esos `width/height/label` sean el tamaño del
  bloque incrustado en la nota; REA no ejecuta ni resuelve los valores.

### 3.2 `e.prototype.updateSearch` — búsqueda (F05)

- Rango **[2439711, 2440945)**, sha `786ea2aa…f300aab4`.
- REA observó: `calls` (1), `reads-property`, `reads/writes/defines/captures`
  (filas por función en `sources_with_relations`); trace `ev_92a9b9…` resolvió
  módulo + export `default`.
- Complementos en el mismo corpus: `e.prototype.applySearchFilter` (reads),
  `e.prototype.getSearchCursor` (**4 calls, argument-to-parameter 8,
  returns-to-call 6**) y literales `0`.
- **Lectura funcional (observada):** la búsqueda delega en **llamadas a
  funciones** y opera sobre **propiedades** (cursor, filtro), no sólo sobre una
  subcadena; `getSearchCursor` devuelve un objeto/cursor a la llamada.
- **Inferencia:** que ese cursor corresponda a «coincidencias con contexto».
  La semántica exacta del cursor es *desconocida* (no ejecutada).

### 3.3 `e.prototype.startHover` — preview al pasar el mouse (F01)

- Rango **[526155, 526647)**, sha `f0dcc012…8d0ca14`.
- REA observó literales **`-1` y `1`** y múltiples `reads-property`.
  Vecinas: `e.prototype.activateHover` (rango **[526674, 527032)**) con
  **`creates-promise` → `Promise.then`**; `t.prototype.showPreview`
  (**[2630253, 2630533)**) con literal `false`.
- **Lectura funcional (observada):** el arranque del hover usa índices/sentinelas
  (`-1`, `1`); la **activación** del hover es asíncrona (`Promise.then`). El
  patrón «hover → activación diferida → mostrar preview» queda respaldado por
  tres funciones del corpus.

### 3.4 `t.prototype.findCurrentOutlineItem` — esquema (F13)

- Rango **[2651659, 2652315)**, sha `a53878d9…30ff8f3`.
- REA observó `writes` (10), `reads` (19), `reads-property` (8), `defines` (19),
  `captures` (25); trace `ev_557076…` resolvió módulo + export `default`.
  Vecinas: `renderOutline`, `extractHeading`, `getHeadingRange`,
  `findActiveHeading`, `foldAllHeadings`, `createGroupHeadingEl`.
- **Lectura funcional (observada):** hay un componente de esquema que **localiza
  el ítem activo**, **extrae encabezados**, **calcula su rango** y **renderiza**
  un árbol colapsable. Es decir: outline de **encabezados del documento**, con
  seguimiento de la posición actual.

### 3.5 `t.prototype.computeFileMetadataAsync` — metadatos (F07)

- Rango **[1765882, 1768094)**, sha `1a057fba…6c308dcf`.
- REA observó: **`writes-property` → `metadata`, `size`, `mtime`, `label`,
  `hash`** (6) y —clave— **`schedules-timer` → `setTimeout`** y
  **`cancels-timer` → `setTimeout`** (1 cada uno). El nodo `timer` no es genérico:
  REA registró el rango exacto `[l.11, col 1576–1655]`.
- **Lectura funcional (observada):** el cálculo de metadatos **agenda y cancela un
  temporizador** (patrón de *debounce*), y **escribe** un objeto con
  tamaño/fecha/hash. `t.fromFrontMatter` (**[2206018, 2206450)**) y
  `e.prototype.processFrontMatter` dan la contraparte de frontmatter.
- **Inferencia:** que el temporizador sirva para agrupar ediciones (debounce) y
  no para otra finalidad; el propósito exacto del timer es *desconocido*.

### 3.6 Hallazgos adicionales (misma calidad de evidencia)

| Función | Rango `app.js` | sha fragmento | REA observó |
|---|---|---|---|
| `t.prototype.triggerWikilink` | [2571072, 2571337) | `ecfe167f…973a2687` | **literales `"[["` y `"![["`** — sintaxis de wikilink y **bang-wikilink (embed)** |
| `e.prototype.insertCallout` | [1728844, 1729477) | `9fb53f38…392d9380` | `writes-property` → `line` (2) — inserción de callout |
| `e.prototype.addHistoryItem` | [2981689, 2982320) | `da56d4c1…a9cf62b` | `writes-property` → `id` — identidad de ítem de historial |
| `e.prototype.navigateMedia` | [1700918, 1702313) | `09b9d601…9dc671fe7` | literales `"20%"`, `"-20%"` — salto porcentual en media |
| `t.prototype.renderProperties` | [2486959, 2488531) | `ae780594…4b22eb9` | `calls` ×2, `returns-to-call` ×2, `argument-to-parameter` ×2 |
| `e.prototype.restoreNavigation` | (nav_history) | — | `schedules-timer` setTimeout + literal `true` |

Colectivamente, el corpus contiene **14 nodos `literal`**, **3 `timer`** y
**2 `promise`** con rangos exactos; esos nodos son la evidencia funcional más
fuerte (valores concretos que REA leyó del código, no adivinados).

### 3.7 Límite explícito de estos hallazgos

REA **no** probó ejecución, activación por defecto, ni configuración. Un
`writes-property` significa «la función escribió esa propiedad *en el código*»,
no «esa propiedad existe en runtime». Los traces devolvieron `paths` terminales 0
porque el corpus no modela importaciones entre módulos (§6).

---

## 4. Separación explícita: REA / otra / inferencia / propuesta

- **Observado por REA (estático):** rangos + relaciones semánticas + literales +
  timers/promesas de §2-3; nodos, aristas y fingerprints; resolución de semillas
  de los 4 traces.
- **Otras herramientas (no REA):** aislamiento AST y digests (`@babel/parser`,
  `node:crypto`); inventario del ASAR e i18n `es` de la investigación previa;
  lectura del repo Glosa.
- **Inferencia:** el *significado* de cada relación en términos de UX (p. ej.
  «el embed mide su contenedor») y la correspondencia Obsidian→Glosa.
- **Propuesta:** cada `adaptacion` / `aceptacion` del inventario; **nada** está
  implementado y **nada** se respalda con ejecución.

En Glosa se leyó, sin modificarlo: `README.md`, `docs/evaluacion-rigurosa.md`,
`docs/herramientas-estudio.md`, `web/study-tools.js` (normalizeTitle L97,
extractWikilinks L105, findNoteByTitle L116, getBacklinks L126),
`web/markdown.js` (heading L21, blockquote L31), `web/notes.js`. La regla de
evaluación rigurosa se aplicó: **leer, autoevaluarse o marcar no acreditan
dominio**, así que los beneficios se formulan como **hipótesis** y cada feature
exige un **criterio de aceptación verificable aparte**.

---

## 5. Inventario (resumen)

`inventario.json` — **20 funcionalidades** relevantes a Glosa, con
`id, nombre, observado_en_target, origen_evidencia, evidence_ids, rutas_rangos,
estado_glosa, adaptacion, prioridad, riesgo, aceptacion`.

- Origen: **REA = 14**, **otra = 6**, **inferencia = 0** por entrada (la
  inferencia se declara dentro de cada `observado_en_target`/`aceptacion`).
- Estado en Glosa: existe 3, parcial 7, nuevo 9, desconocido 1.

| id | Funcionalidad | Origen | Estado Glosa | Prioridad |
|---|---|---|---|---|
| F01 | Preview al hover | REA | parcial | media |
| F02 | Wikilinks `[[]]` | REA | existe | baja |
| F03 | Embeds/transclusión `![[]]` | REA | parcial | media-alta |
| F04 | Callouts `> [!]` | REA | nuevo | alta |
| F05 | Búsqueda con contexto | REA | parcial | alta |
| F06 | Autocompletado de enlaces | REA | nuevo | media |
| F07 | Metadatos frontmatter | REA | parcial | media |
| F08 | Panel de propiedades | REA | parcial | media |
| F09 | Resolución de enlaces | REA | parcial | media |
| F10 | Referencias inversas | REA | existe | baja |
| F11 | Historial de navegación | REA | desconocido | media |
| F12 | Navegación/media | REA | parcial | baja |
| F13 | Esquema del apunte | REA | nuevo | alta |
| F14 | Generación de enlaces MD | REA | parcial | baja |
| F15 | Fórmulas MathJax | otra | nuevo | media-alta |
| F16 | Notas al pie | otra | nuevo | media |
| F17 | Panel de etiquetas | otra | nuevo | media |
| F18 | Mermaid | otra | nuevo | baja |
| F19 | Vista previa PDF | otra | existe | baja |
| F20 | Marcadores a repasar | otra | nuevo | media-alta |

(F15-F20 provienen de bibliotecas/i18n del inventario del ASAR, **no** del
corpus REA reducido; se marcan como `otra` y no como hallazgo REA.)

---

## 6. Incógnitas honestas

1. **Cobertura, no ausencia.** El corpus cubre 90 funciones; la app tiene 15 442
   funciones nombradas. Fuera del corpus, las familias `call-flow`/`data-flow`/
   `object-flow` quedan *unknown* (REA lo declara). No se afirma nada sobre lo no
   incluido.
2. **Sin ejecución.** Cero observación runtime; no se valida activación por
   defecto, ajustes, ni rutas de código en producción.
3. **`paths` terminales = 0** en los 4 traces: el corpus no modela el árbol de
   `import`/bundler real; las trazas confirman identidad y `exposes default`,
   no cadenas de llamadas entre módulos.
4. **`modules: 0`** y `module_format: commonjs`: el contenedor del corpus hace
   que los exports aparezcan como `default`; no refleja los `export` originales.
5. **Contexto de módulo ausente:** variables externas minificadas de `app.js` no
   se resuelven dentro del corpus (declarado). Algunas `aliases` quedan
   `candidate`, no `resolved`.
6. **Discrepancia de hash previa** (`app.js` `c6df46ee…` vs `958ce57f…`) sigue
   sin conciliar; se usa el valor reproducible de esta extracción.
7. **`statistics.findings = 94`** se reporta como conteo de REA; el arreglo de
   findings no se materializó en el JSON canónico de salida (sólo aparece el
   conteo). No se interpretan como hallazgos individuales.
8. **Fuera de alcance:** plugins de comunidad, bóvedas, datos personales,
   publicar/sync. No se leyeron.

---

## 7. Artefactos (`/tmp/glosa-deep-20261017/obsidian/`)

| Ruta | Contenido |
|---|---|
| `informe.md` | Este informe |
| `inventario.json` | 20 funcionalidades + referencias de evidencia |
| `corpus/` (90 `.js`) + `corpus/INDEX.json` | Corpus derivado reducido con rango/digest/transformación |
| `tools/extract_functions.mjs` | Extracción AST reproducible |
| `tools/summarize.mjs`, `tools/build_inventory.mjs` | Resumen REA e inventario |
| `evidence/re05-corpus-analysis.json` | Evidencia REA `ev_87d26e1f…` completa |
| `evidence/re05-summary.json` | Resumen compacto de relaciones por función |
| `evidence/trace-<n>.json` (+ `-input.json`) | 4 trazas REA (`ev_2f0661…`, `ev_92a9b9…`, `ev_278724…`, `ev_557076…`) |
| `evidence/view-loadEmbed.json` (+ `-input.json`, `-loadEmbed.log`) | Vista REA del módulo `loadEmbed` (`ev_2a62d6db…`; `complete-within-view`) |
| `evidence/HASHES.txt` | Hashes de target, corpus y evidencias |

---

## Resumen final

- **REA sí produjo resultado funcional verificable:** corpus reducido de 90
  funciones reales (rango+digest verificados 90/90) analizado por
  `analyze-javascript-application` → **13 037 relaciones semánticas** y
  **212 fingerprints** (`ev_87d26e1f…`), más **4 trazas**
  `trace-application-feature` y **1 vista** `inspect-analysis-view`
  (`ev_2a62d6db…`).
- **≥5 funciones profundizadas con evidencia REA:** `loadEmbed` (writes
  width/height/label + Promise), `updateSearch` (calls/reads-property + cursor),
  `startHover`/`activateHover` (literales + Promise.then), `findCurrentOutlineItem`
  (outline con rango de encabezado), `computeFileMetadataAsync` (writes
  metadata/size/mtime/hash + schedule/cancel setTimeout); y adicionales:
  `triggerWikilink` (literales `"[["`/`"![["`), `insertCallout`, `addHistoryItem`,
  `navigateMedia`, `renderProperties`.
- **Entregables:** `informe.md`, `inventario.json` (20 funcionalidades: 14 REA,
  6 otra) y `evidence/`.
- **Bloqueos:** sin runtime; corpus no modela importaciones (`paths` 0);
  contexto de módulo ausente; findings=94 sin arreglo. Glosa no fue modificado.
