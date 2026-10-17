> Informe original de DeepSeek; ver [síntesis y revisión](README.md) para correcciones y prioridades finales. Las rutas de evidencia del agente corresponden a `/tmp/glosa-obsidian-research`.

# Obsidian → Glosa: features para preparar parciales

Investigación y propuestas. **No se implementó ningún cambio.** No se tocó el
repositorio de Glosa, ni bóvedas, ni datos reales.

- Modelo: **DeepSeek V4.1 Flash Free** (proveedor OpenCode). Sin delegación a
  otros modelos ni a otros proveedores; sin consultas pagas; sin navegación web.
- Fecha: 2026-10-17.
- Salida: `/tmp/glosa-obsidian-research/` (informe + `evidence/`).

---

## 1. Metodología, comandos ejecutados, evidencia y límites

### 1.1 Flujo seguido (skill REA)

Se siguió `reverse-engineer-anything/SKILL.md`: enrutar el objetivo (ASAR/Electron →
`analyze_javascript_application`), trabajar **summary-first**, no repetir análisis,
y distinguir observación / inferencia / incógnita. Como el análisis general de
`obsidian.asar` ya había agotado antes la ventana («agotó 30 segundos», según
`docs/obsidian-note-preview.md`), **no lo repetí igual**: usé alcance reducido
(timeout ampliado + heap), extracción de miembros del ASAR con offsets/hashes y
grep focalizado, que es la vía que la skill recomienda cuando el análisis general
no alcanza.

### 1.2 Comandos realmente ejecutados

1. `sha256sum /usr/lib/obsidian/{obsidian.asar,app.asar,icon.png}` y
   `stat` de tamaños.
2. `rea --version` → `rea@6.4.0`.
3. **Operación REA real #1 (análisis general, no completó):**
   `rea analyze-javascript-application /usr/lib/obsidian/obsidian.asar
   --max-heap-mb 2048 --analysis-timeout-ms 240000 --format json`
   → error de ejecución con **observación parcial** retenida:
   `ev_666da72795dc1cd5730926fb3d660c498b45759f4917064530c93b5c01a9dceb`.
   El adaptador `javascript-static-analysis` falló en fase `semantic` con
   `SIGTERM` sobre `app.js` (no fue timeout declarado por la CLI).
4. **Operación REA real #2 (completó):**
   `rea analyze /usr/lib/obsidian/app.asar --format json`
   → `ev_59d450728ffd97f380c2653460c60b1f4b34d7abd0fe0eb85e9975121aa0d053`
   (shell Electron: inventario, IPC, handlers; ver §1.4).
5. Parseo del **header del ASAR** en Python (solo lectura): `BASE = 8 + headerSize
   = 95924`; inventario de 368 miembros con tamaño y offset. Extracción de
   miembros concretos por offset con hash reproducible (`evidence/hashes.txt`).
6. `grep`/`find` focalizados sobre `app.js`, `app.css`, `i18n/es.txt` extraídos,
   con offsets de byte citados abajo.

### 1.3 Evidencia REA (IDs y hashes)

| Ítem | Valor |
|---|---|
| `obsidian.asar` SHA-256 | `146ef8470d8cbb4a6db209bdc19bf2bad13350444186c0fd93c31087b142b92f` (27 477 966 B) |
| `app.asar` SHA-256 | `2b50b52ddab21f81ca113e6b6f3ce83b0274aa6fa3a7e09f99d779c159fe4492` (73 695 B) |
| REA obsidian.asar (parcial) | `ev_666da72795dc1cd5730926fb3d660c498b45759f4917064530c93b5c01a9dceb` |
| REA app.asar (completa) | `ev_59d450728ffd97f380c2653460c60b1f4b34d7abd0fe0eb85e9975121aa0d053` |
| Análisis previo (doc del repo) | `ev_7321f17c…` / resumen `ev_c73b9af5…` (`docs/obsidian-note-preview.md`) |
| `app.js` extraído | 3 942 126 B, SHA-256 `958ce57fe22f87fdf121546e46dfccd9c8ee971ce3fd8f801d60d4ece39a2df9` |
| `i18n/es.txt` extraído | 88 438 B, SHA-256 `299edf9ae857b3af56dde7524d6c89cbd6ceda9fb4ce608fddf541359f425595` (2 601 líneas) |
| `app.css` extraído | 668 223 B, SHA-256 `866e50ac84dd8ad2775e0047ebd3ec5bd03e5af722aff259e6c4ea3cec42d7ba` |
| `lib/mathjax/obsidian-mathjax.js` | 1 139 224 B, SHA-256 `ac00d774…` |
| `lib/mermaid.min.js` | 2 964 042 B, SHA-256 `6ef73c97…` |
| `lib/pixi.min.js` | 487 134 B, SHA-256 `842814b2…` |

Offsets de byte citados en este informe (todos dentro de los archivos extraídos,
y su equivalente dentro de `obsidian.asar` sumando la base del miembro `app.js`,
offset 668 223, más `BASE` 95 924 → **+764 147**):

- `[!` (inicio de sintaxis de callout): byte **181 953** en `app.js` → **946 100** en el ASAR.
- `callout` (tokenizador de blockquote): byte **182 460** → 946 607.
- `mermaid.initialize(...)`: byte **1 998 940** → 2 763 087.
- `yE("/lib/mathjax/obsidian-mathjax.js"…)`: byte **2 000 056** → 2 764 203.
- `loadMathJax / loadMermaid / loadPdfJs / loadPrism` (export list): byte **255 610** → 1 019 757.
- `popover hover-popover` / `onHoverLink`: bytes **2 424 650** y **3 527 203** → 3 188 797 y 4 291 350
  (coinciden con `docs/obsidian-note-preview.md`).

### 1.4 Qué devolvió cada operación REA

- **`ev_666da7…` (obsidian.asar, parcial).** Inventario de 38 archivos relevantes,
  16 558 635 B de texto leído, 1 123 389 nodos AST visitados, **103 findings**,
  pero **1 archivo JS parseado** y **0 módulos** resueltos: la fase semántica se
  interrumpió, así que **no hay grafo de módulos ni relaciones IPC/preload fiables**
  de esta corrida. El grafo contiene 163 nodos (38 `asar-entry`, 32 `javascript-asset`,
  22 `endpoint`, 17 `storage`, 5 `worker`, 3 `javascript-module`, 1 `electron-preload`)
  y 219 aristas, con `coverage.status = "partial"`. Limitaciones declaradas por REA
  (textuales, abreviadas): «Graph coverage is incomplete… must not be read as
  absence», «JavaScript and HTML were parsed as inert text; bundle bootstrap code
  was never executed», «Source analysis was interrupted».
- **`ev_59d450…` (app.asar, completa).** El shell Electron se analizó entero
  (handlers IPC, transmisiones, estructura de bundler). Es evidencia del
  contenedor Electron, **no** del conjunto de features del renderer.
- **Extracción directa.** El inventario del ASAR enumera librerías empaquetadas
  (`lib/mathjax`, `lib/mermaid.min.js`, `lib/pixi.min.js`, `lib/pdfjs`,
  `lib/prism.min.js`, `lib/codemirror`, `lib/reveal/reveal.js`, `quicklook.js`,
  `worker.js`) e internacionalización (`i18n/*.txt`, 60+ idiomas).

### 1.5 Tipos de evidencia y límites (importante)

- **Estático (comprobado):** presencia de librerías, clases CSS, cadenas de
  localización `es` y literales en `app.js`, con hash y offset reproducibles.
- **Observado en runtime: NADA.** No se arrancó Obsidian, no se abrió ninguna
  bóveda, no hubo captura de proceso ni de Electron. Ninguna afirmación de este
  informe describe comportamiento en ejecución.
- **Inferido (declarado como tal):** que una cadena/clase/librería empaquetada
  corresponda a una función activada por defecto. La i18n también incluye textos
  de *publicar* y de opciones; presencia ≠ activación.
- `app.js` es un bundle minificado (≈3,9 MB). **No se copió implementación
  propietaria**; solo se citan marcadores, offsets y el significado funcional.
- **Discrepancia abierta:** `docs/obsidian-note-preview.md` atribuye a `app.js`
  el SHA-256 `c6df46ee…`; mi extracción (misma base de header, offsets que
  reproducen las posiciones del ASAR documentadas) da `958ce57f…`. No pude
  conciliar ambas cifras; uso la mía, que es reproducible y consistente con los
  offsets, y la señalo como límite.
- Fuera de alcance: complementos de la comunidad, bóvedas, plugins de repetición
  espaciada (no son núcleo de Obsidian) y cualquier dato personal.

---

## 2. Propuestas priorizadas (9)

Convención: **[E]** = evidencia de Obsidian; **[G]** = estado real de Glosa;
**[I]** = interacción del estudiante; **[H]** = beneficio esperado (**hipótesis**,
no promesa de aprendizaje); **[A]** = adaptación mínima; **[R]** = dificultad/riesgo;
**[C]** = criterio de aceptación verificable. Ordenadas de mayor a menor prioridad
de arranque (ver §3).

### P1 — Búsqueda en las notas con contexto y operadores

- **[E]** Obsidian tiene búsqueda con operadores y contexto: i18n `es` 1253
  «buscar por etiquetas», 1254 «buscar palabras clave en la misma línea», 1255
  «buscar palabras clave bajo el mismo encabezado», 1258 «Buscar en la carpeta»,
  1222 «Coincide con el bloque:» y 1192 «Buscar en todos los archivos»
  (`evidence/obsidian-i18n-features-es.txt`). Es una capacidad central y
  verificable en cadena de UI.
- **[G]** Hoy la búsqueda es un `includes()` de subcadena sobre `title + content +
  pageNotes`, filtrada por carpeta, sin contexto ni operadores:
  `web/notes.js:317-319` (y el input en `web/notes.js:362`). Las «Menciones»
  (`web/study-tools.js:145-170`) solo buscan el **título exacto** de la nota.
- **[I]** Antes de un parcial escribís un término (p. ej. «regla de la cadena») y
  ves **una fila por aparición** con su encabezado y una línea de contexto, en
  apuntes, clases y ejercicios; un clic abre el lugar.
- **[H]** Reduce el riesgo de «perder el hilo» al localizar un concepto entre
  fuentes dispersas y ahorra tiempo de recorrido manual. *(Hipótesis.)*
- **[A]** Reutilizar el `snippet()` existente (`web/study-tools.js:98-103`) para
  producir el fragmento; extender la lista lateral con una vista de resultados.
  Sin backend nuevo: el estado ya tiene todas las notas y cursos en memoria.
- **[R]** Media. Riesgo: rendimiento con notas grandes; mitigar con límite de
  resultados y debounce.
- **[C]** Buscar un término devuelve una fila por aparición con encabezado y
  contexto; un término ausente muestra «sin resultados» explícito; los filtros
  vacíos siguen incluyendo notas sin propiedades; prueba en navegador real.

### P2 — Callouts para fichas y registro de errores

- **[E]** Callouts de Obsidian comprobados: `app.js` byte 181 953 contiene el
  analizador `/^\[!([^\]]+)\]([+\-]?)(?:\s|$)/` dentro del tokenizador de
  blockquote, y en byte 182 460 produce `{type:"blockquote", …, callout:A}`
  (`evidence/obsidian-appjs-markers.txt`); `app.css` contiene 72 coincidencias de
  `.callout` más `callout-title/content/icon/color`; i18n tipos de callout en 2542-2549
  (Información, Importante, Consejo, Éxito, Pregunta, Advertencia, Cita, Ejemplo).
- **[G]** La plantilla de ficha usa encabezados planos `## Ficha:` y `###` por
  sección (`web/study-tools.js:26-42`), y los errores se listan como `article`
  (`web/study-tools.js:542-553`). El render Markdown solo conoce `blockquote`
  genérico (`web/markdown.js:31`), sin tipos.
- **[I]** Al insertar una ficha, sus secciones **Definición / Ejemplo /
  Contraejemplo / Fuente / Pregunta** se ven como bloques con color e ícono; el
  contraejemplo y el error se distinguen de la definición de un vistazo.
- **[H]** Mejora el escaneo visual del material de repaso y la separación entre
  «lo correcto» y «mi error». *(Hipótesis.)*
- **[A]** Añadir un caso `callout` al renderer (`web/markdown.js`) y CSS. No hace
  falta tocar el editor: el editor en vivo usa el mismo renderer
  (`web/editor/live.js:41`).
- **[R]** Baja-media. Riesgo: que un `blockquote` normal cambie de aspecto;
  limitar a bloques que empiecen con `[!`.
- **[C]** Un bloque `> [!contraejemplo] …` produce un callout con su etiqueta; un
  `> cita` normal sigue siendo `blockquote`; prueba de render + navegador.

### P3 — Esquema (outline) del apunte por encabezados

- **[E]** i18n `es` 1541-1546 («Esquema… Muestra el esquema del archivo actual o
  el panel enlazado») y 1665 («Mostrar el esquema de encabezados»). Verificado en
  la tabla de features.
- **[G]** El único «índice» es de **lecciones** del curso (`web/index.html:12`,
  `web/keyboard.js:60,140`), no de encabezados del apunte. `notes.js` no genera
  outline. Un apunte largo (ficha + errores + anotaciones) no tiene navegación
  interna.
- **[I]** Abrís un apunte largo y saltás por Ficha / Definición / Contraejemplo /
  Errores sin desplazarte.
- **[H]** Menos fricción para releer material extenso antes de un parcial.
  *(Hipótesis.)*
- **[A]** Extraer encabezados del contenido (regex de `^#{1,6} `) y listarlos en
  el panel de estudio o en una barra; reusar estilos existentes.
- **[R]** Baja.
- **[C]** El esquema lista encabezados en orden con su nivel; el clic lleva al
  punto; se actualiza al cambiar de apunte; apunte sin encabezados muestra aviso.

### P4 — Alias de apunte para enlaces `[[…]]`

- **[E]** i18n `es` 944 «Añadir alias» y 2490 «Alias»; `app.js` exporta
  `parseFrontMatterAliases` (lista de exports, byte 255 610). Obsidian resuelve
  enlaces internos por título **o alias**.
- **[G]** `findNoteByTitle` compara **título exacto normalizado** y nada más
  (`web/study-tools.js:116-120`); la limitación está declarada en
  `docs/herramientas-estudio.md:34-35,172-175`. Las claves de frontmatter ajenas
  se conservan pero no se usan (`note_files.py:335-338,427-428`).
- **[I]** Enlazás `[[Derivada]]` y resuelve a la nota «Reglas de derivación»
  porque definiste ese alias; las referencias inversas se calculan igual.
- **[H]** Menos enlaces rotos y menos fricción al escribir títulos largos; mejora
  la red de relaciones entre apuntes. *(Hipótesis.)*
- **[A]** Agregar `aliases` a la metadata de estudio (validada en
  `library.py:284-321`), un campo en la pestaña Propiedades y usarla en la
  resolución de `study-tools.js`.
- **[R]** Media (validación + resolución + UI + tests).
- **[C]** Un `[[alias]]` resuelve a la nota correcta; las referencias inversas
  incluyen enlaces por alias; un alias inexistente se reporta «no existe»; sin
  ambigüedad si dos notas comparten alias (mostrar desambiguación).

### P5 — Transclusión de fichas (`![[Título]]`)

- **[E]** i18n `es` 2051 «Incrustar nuevo archivo», 1101 «Insertar adjunto…»,
  2230 «a bloque incrustado»; `app.js` contiene el literal `![[` (primeras
  apariciones en offsets 789 225, 1 725 972, …) y `app.css` define
  `.markdown-embed` (58), `internal-embed` (8) y `.cm-embed` (5).
- **[G]** Existe el enlace nativo a nota `[texto](#note=id)` y su **vista previa
  hover** (`web/app.js:185-221`, documentado en `docs/obsidian-note-preview.md`),
  pero el contenido **no se incrusta**: los `[[wikilinks]]` solo se listan en el
  panel (`web/study-tools.js:105-135`), no se renderizan ni transcluyen.
- **[I]** En el apunte «Repaso parcial» incrustás `![[Ficha: Derivada]]` y ves la
  ficha completa, que se actualiza sola al editarla en su nota original.
- **[H]** Una sola fuente de verdad por concepto, sin copias divergentes.
  *(Hipótesis.)*
- **[A]** Reusar `NoteMarkdown.render` para el cuerpo incrustado (ya existe el
  renderer de preview); manejar `![[Título]]` y `![[Título#^id]]` con **límite de
  profundidad** para evitar recursión.
- **[R]** Media-alta (recursión, bucles, rendimiento).
- **[C]** `![[X]]` muestra el contenido de X en solo lectura con enlace a abrir;
  destino inexistente → aviso; auto-embed no cuelga (profundidad acotada);
  prueba de render.

### P6 — Fórmulas matemáticas (LaTeX/MathJax)

- **[E]** El ASAR incluye `lib/mathjax/obsidian-mathjax.js` (1 139 224 B) y fuentes
  `lib/mathjax/tex-font/...`; `app.js` lo carga
  (`yE("/lib/mathjax/obsidian-mathjax.js"…)`, byte 2 000 056) y exporta
  `loadMathJax` (byte 255 610); i18n `es` 626 «Bloque matemático», 635 «Fórmula
  matemática», 489-490 «Alternar bloque de ecuación». Verificado por ruta del
  miembro en el inventario del ASAR.
- **[G]** `web/markdown.js:19-51` no tiene caso de matemática: `$x^2$` cae a texto
  o `codespan`. No hay render de fórmulas en apuntes ni en preview.
- **[I]** Escribís y leés fórmulas en apuntes de Análisis/Física; la ficha de un
  concepto puede mostrar la fórmula.
- **[H]** La notación correcta evita ambigüedad frente a texto plano.
  *(Hipótesis.)*
- **[A]** Empaquetar un renderer local (**sin CDN**, por privacidad) y agregar los
  casos `inlineMath`/`displayMath` al renderer; mismo camino para el editor en vivo.
- **[R]** Alta. Riesgo: tamaño del bundle, costo de render en listas, sanitización.
- **[C]** `$x^2$` y `$$…$$` renderizan; un `$` literal no rompe la nota; **cero**
  requests de red (verificable); nota sin fórmulas no cambia.

### P7 — Notas al pie para citar fuentes

- **[E]** i18n `es` 628/992/1105 «Nota al pie», 536 «Borrar nota al pie y su
  referencia», 1398 «La nota al pie {{id}} no se encontró…»; `app.js` contiene el
  literal `[^` (marcador de nota al pie).
- **[G]** Glosa permite **anclas** a páginas de PDF con `quote`, `page` y `sha256`
  (`library.py:254-275`) y la ficha tiene una sección `### Fuente` libre
  (`web/study-tools.js:37-38`), pero el cuerpo del apunte no tiene sintaxis de
  nota al pie.
- **[I]** Escribís «… regla de la cadena[^1]» y una nota `[^1]: Kreyszig, p. 214`
  que enlaza a la fuente sin cortar el texto.
- **[H]** Mantiene el hilo de lectura y conserva la trazabilidad a la fuente.
  *(Hipótesis.)*
- **[A]** Extender `web/markdown.js` y el editor en vivo con el token de nota al
  pie; mostrar referencias no resueltas en vez de ocultarlas.
- **[R]** Media.
- **[C]** El marcador enlaza a su definición y viceversa; una referencia sin
  definición se marca visiblemente; texto con `[^` no intencional no rompe.

### P8 — Marcadores de bloques a repasar, integrados al Plan

- **[E]** i18n `es` 1404/1421/1440 «Marcadores/Marcador» y 1413 «Marcar bloque
  bajo el cursor…»; 522 «para enlazar bloques». (Obsidian llama a esto
  Bookmarks; el marcado por bloque está verificado.)
- **[G]** Existe `needsPractice` bool por apunte (`web/study-tools.js:88-89`, 507)
  y un plan global ordenable por puntaje explicable (`web/plan.js`,
  `docs/modos-tutor.md:66-91`), pero **no** se puede marcar un tramo concreto
  (una sección de ficha, un error) para repasarlo.
- **[I]** Marcás la sección «Contraejemplo» de una ficha; antes del parcial, la
  pestaña **Parciales** del Plan reúne tus bloques marcados.
- **[H]** Concentra el repaso en los tramos flojos en vez de en la nota entera.
  *(Hipótesis.)*
- **[A]** Guardar marcadores (título + posición) en la metadata de estudio
  (`library.py:284-321`) y listarlos en el panel de estudio y en Plan.
- **[R]** Media-alta.
- **[C]** Marcar un bloque lo lista en el repaso; desmarcarlo lo quita; persiste
  en la metadata de la nota y sobrevive a la recarga.

### P9 — Etiquetas de concepto/error con panel de etiquetas

- **[E]** i18n `es` 1354 «Panel de Etiquetas», 1355/1297 «Etiquetas», 555 «Buscar
  etiqueta», 1358 «Etiquetas no encontradas»; `app.css` define `.tag`,
  `.tag-pane-tag`, `.tag-container`, `.tag-pane-tag-count`; i18n 1253 «buscar por
  etiquetas».
- **[G]** No hay etiquetas en el cuerpo. La clasificación es `materia`/`unidad`
  (texto libre) y `errorType` (enum: concepto/procedimiento/cálculo/…)
  (`library.py:286`, `web/study-tools.js:25`), sin marcas transversales.
- **[I]** Marcás `#error-de-signo` o `#teorema` en el cuerpo; un panel lista las
  etiquetas con su conteo y enlaza a las notas/errores.
- **[H]** Hace visibles patrones de error recurrentes entre apuntes (más que
  organizar carpetas). *(Hipótesis.)*
- **[A]** Parser de `#etiqueta` en el texto + panel que reusa el panel de estudio;
  las etiquetas **no** crean cursos ni evaluaciones.
- **[R]** Media-alta. Riesgo: que derive en «organización por organización»; acotar
  a marcas de concepto/error y a la vista de repaso.
- **[C]** Las etiquetas se extraen del cuerpo; el panel muestra conteo y abre el
  origen; filtrar por etiqueta no altera cursos ni eventos de evaluación.

---

## 3. Tres prioridades para empezar y tres cosas que NO conviene trasladar

### Empezar por (orden sugerido)

1. **P1 · Búsqueda con contexto y operadores.** Es el mayor hueco cotidiano para
   «consultar fuentes sin perder el hilo»; ya existen todas las piezas
   (`snippet()` en `study-tools.js`, estado en memoria) y no agrega dependencias
   ni riesgo de datos. Alto valor por bajo costo.
2. **P2 · Callouts para fichas y errores.** Refuerza justo lo que Glosa ya hace
   (ficha de concepto y registro de errores); es un cambio acotado en el renderer
   (`markdown.js`) más CSS, y mejora la lectura de repaso de inmediato.
3. **P3 · Esquema del apunte.** Barato, sin dependencias, y ataca la navegación de
   apuntes largos, que es un cuello de botella real antes de un parcial.

*(P6 · Fórmulas es el mayor valor para materias con matemática, pero lo dejaría
para una segunda etapa por el costo de empaquetar el renderer sin CDN; conviene
decidir antes la política de dependencias y tamaño.)*

### NO conviene trasladar para este propósito

1. **Vista gráfica global / gráfico de la bóveda** (i18n 1280-1286; `lib/pixi.min.js`
   empaquetado). Es vistoso pero no entrena recuperación ni aplicación; consume una
   dependencia gráfica pesada. Si hace falta «comprender relaciones», basta una
   **lista** de enlaces entrantes/salientes y menciones, que Glosa ya tiene
   (`web/study-tools.js:126-170`).
2. **Canvas / lienzo infinito** (i18n 2142+, 2191-2270). Traslada el esfuerzo del
   estudio a *administrar un tablero*; no aporta a practicar recuperación. El
   propio `docs/inspiracion.md:16-19` ya ubica el «mapa de conceptos» como algo
   posterior y opcional, sin volverlo eje.
3. **Sincronizar / Publicar** (i18n 1600s y 1930s). Glosa es local (loopback +
   Tailscale Serve privado, `docs/acceso-remoto.md`, `README.md:24`). Agregar un
   backend de sync/publicación contradice el alcance de privacidad y no mejora la
   preparación del parcial.

*(Nota, sin prometerlo como feature de Obsidian: la **repetición espaciada** no es
núcleo de Obsidian —no aparece como tal en la i18n—; si se quiere, corresponde
diseñarla desde Glosa sobre `needsPractice`, errores y el Plan, no «traerla» de
Obsidian.)*

---

## 4. Qué no pudo verificarse y artefactos de evidencia

### 4.1 Incógnitas y límites

- **El análisis semántico completo de `obsidian.asar` no terminó** (`SIGTERM` en
  fase `semantic` sobre `app.js`): **0 módulos, 0 factos de IPC/preload y 0
  ventanas** en esa corrida. El grafo quedó `partial`; REA advierte que lo
  ausente «no debe leerse como ausencia». No se repitió la misma corrida.
- **Nada observado en runtime.** Ninguna propuesta se apoya en comportamiento
  observado de Obsidian; todo es estático o inferido.
- **`app.asar`** se analizó completo, pero solo describe el shell Electron.
- **Discrepancia de hash** de `app.js` respecto de `docs/obsidian-note-preview.md`
  (`c6df46ee…` vs `958ce57f…`), sin resolver; los **offsets** sí son consistentes
  con las posiciones del ASAR allí documentadas.
- **Presencia ≠ activación.** No se probó que MathJax/Mermaid/Pixi/Reveal estén
  inicializados en una instalación por defecto, ni qué ajustes los habilitan.
- **Observaciones fuera de alcance:** complementos de la comunidad, bóvedas,
  plugins (p. ej. repetición espaciada), datos personales. No se leyeron.
- En Glosa, las referencias de línea corresponden a esta fecha; pueden moverse
  con ediciones futuras. No se ejecutó la suite de tests de Glosa.

### 4.2 Artefactos bajo `/tmp/glosa-obsidian-research/`

| Ruta | Contenido |
|---|---|
| `informe-deepseek.md` | Este informe |
| `evidence/hashes.txt` | Hashes de originales, extraídos y resultados REA |
| `evidence/re01-obsidian.asar-summary.json` | Salida cruda REA del análisis general (envelope de error) |
| `evidence/re01-stderr.log` | Progreso y `SIGTERM` del análisis general |
| `evidence/re02-partial-observation.json` | Observación parcial `ev_666da7…`: inventario, estadísticas, grafo, limitaciones |
| `evidence/re03-inspect-partial-summary.json` | Intento de vista REA (rechazado: faltaban `source`/`view`) |
| `evidence/re04-analyze-app.asar.json` | Análisis REA completo de `app.asar` (`ev_59d450…`) |
| `evidence/re04-stderr.log` | Log del análisis de `app.asar` |
| `evidence/asar-header-listing.txt` | Inventario del ASAR (tamaños/offsets), con base del header |
| `evidence/asar-members-full.txt` | Inventario completo de los 368 miembros |
| `evidence/obsidian_app.js` | `app.js` extraído (con hash y offsets citados) |
| `evidence/obsidian_app.css` | `app.css` extraído (clases `.callout`, `.markdown-embed`, `.tag`) |
| `evidence/obsidian_i18n_es.txt` | `i18n/es.txt` extraído (2 601 líneas) |
| `evidence/obsidian-i18n-features-es.txt` | Cadenas `es` agrupadas por feature con número de línea |
| `evidence/obsidian-appjs-markers.txt` | Ventanas de bytes de los marcadores citados |
| `evidence/obsidian_lib_mathjax_obsidian-mathjax.js`, `obsidian_lib_mermaid.min.js`, `obsidian_lib_pixi.min.js` | Librerías empaquetadas que sustentan P6 y el «no trasladar» #1 |
| `evidence/obsidian_main.js`, `obsidian_worker.js` | Otros miembros inventariados |

### 4.3 Regla de evaluación rigurosa (aplicada a este informe)

Autoevaluación, lectura, marcar o recibir ayuda **no** acreditan dominio: por eso
los beneficios se formulan como **hipótesis** y cada propuesta exige un **criterio
de aceptación verificable aparte**. Las «features de Obsidian» se afirman solo con
evidencia localizable (hash + offset/línea); no se usó ningún LLM como fuente de
azar ni se inventaron estudios o resultados; no se mezcló la validación mecánica
de la cadena de UI con una comprobación semántica de aprendizaje.

---

## Resumen final

- **Modelo:** DeepSeek V4.1 Flash Free (OpenCode); sin delegar ni cambiar de modelo.
- **REA:** 2 operaciones reales (`analyze-javascript-application` sobre
  `obsidian.asar` → parcial `ev_666da7…`; `analyze` sobre `app.asar` → completa
  `ev_59d450…`) más extracción de miembros del ASAR con hash/offset.
- **Entregable:** `/tmp/glosa-obsidian-research/informe-deepseek.md`.
- **Bloqueos:** el análisis semántico completo del `obsidian.asar` no terminó
  (parcial, no repetido); sin observación en runtime; discrepancia de hash de
  `app.js` sin resolver. Glosa no fue modificado.
