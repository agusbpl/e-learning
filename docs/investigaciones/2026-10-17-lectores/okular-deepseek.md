> Informe original de DeepSeek; ver [síntesis y revisión](README.md) para correcciones y prioridades finales. Las rutas de evidencia del agente corresponden a `/tmp/glosa-okular-research`.

# Informe: propuestas para preparar parciales en Glosa, inspiradas en Okular

- Autor: agente `deepseek-v4.1-flash-free` (OpenCode). Encargo delegado, sin implementar cambios.
- Fecha: 2026-10-17.
- Salida: `/tmp/glosa-okular-research/` (este informe) y `.../evidence/`.
- Alcance: investigación **estática**. No se ejecutó Okular ni Glosa; no se abrió ningún
  documento ni el historial real; no se tocó `~/Margen`, `.local-data` ni bases/config
  personales; no se instaló nada; no se usó otro modelo ni otros agentes.

## 0. Resumen ejecutivo

Okular es un lector de PDF maduro: su núcleo expone **índice del documento**,
**marcadores con navegación**, **búsqueda de texto**, **selección** y un **catálogo
de 14 herramientas de anotación** con historial de revisión. Glosa ya tiene lo
esencial para estudiar (apuntes Markdown, resaltados anclados a fragmentos con
huella SHA-256, referencias, fichas, errores, plan de parciales y tutor). Lo que
falta en el **lector de PDF de Glosa** es un conjunto pequeño y concreto de ayudas
de navegación y de repaso.

Siete propuestas, de menor a mayor esfuerzo, priorizan:

1. **Índice del documento anclado a unidades/lecciones** (navegación).
2. **Hoja/panel de repaso por materia y fecha de parcial** (organización de lo ya
   existente: resaltados + errores + plan).
3. **Búsqueda de texto en el lector y en los apuntes** (encontrar, no memorizar).

Ninguna de estas funciones acredita dominio por sí sola: son navegación y
organización. La regla del proyecto (`docs/evaluacion-rigurosa.md`) sigue vigente:
sólo la aplicación independiente evaluada por el tutor puede acreditar dominio.

> Advertencia de evidencia: todo lo que sigue sobre Okular es **estático**
> (símbolos, cabeceras y recursos distribuidos). No se observó su comportamiento en
> ejecución. REA quedó **bloqueado** (ver §5) y no se usó para sostener ninguna
> característica.

---

## 1. Base de evidencia (hashes y rutas)

Identidad de los artefactos inspeccionados (detalle en `evidence/okular-features.md`):

| Artefacto | SHA-256 |
|---|---|
| `/usr/bin/okular` | `7d699b067b6f12d2689cc9a70f8c63f7f2de50b98e02098bbd4ef5c50df01226` |
| `/usr/lib/libOkular6Core.so.4.0.0` | `e011663feccf9977bb33af31cde27540c78a3ac19eab3cbcbad36a9c5944ad08` |
| `/usr/lib/qt6/plugins/kf6/parts/okularpart.so` | `03169aee83484a62935003d9d0a7717adce6cda9aad8d0259d4c90ccb748fa60` |
| `/usr/lib/qt6/plugins/okular_generators/okularGenerator_poppler.so` | `1ef59913223c7e92e29f1ec223857fa7933877961f77c5ee3e15f90e8f6a5d1f` |
| `/usr/share/okular/tools.xml` | `31d62e0da4de032955afca85e292c269f0ba5abff26be9ffcd5d0899e37b7a65` |

Glosa: HEAD `de3f34dc568280d4652d67d15341752efa3efb7e`; pdf.js local `pdfjs-dist 6.4.299`
(`web/vendor/pdfjs/vendor.json`). Estado del repo en `evidence/glosa-state.md`.

Dos símbolos que hacen de “prueba de arquitectura” (importados por el backend PDF,
`evidence/nm-poppler-undef.txt`): `U Okular::DocumentSynopsis::DocumentSynopsis()`
(arma el índice) y `U Okular::TextPage::append(...)` (produce texto para búsqueda y
selección). No se copia implementación propietaria: Okular es GPL, pero el encargo
pide **reconstruir el concepto**, no portar código.

---

## 2. Propuestas priorizadas

### P1 — Índice del documento anclado a unidades y lecciones  ·  [Prioridad 1]

- **Característica comprobada (Okular).** Índice/tabla de contenidos del documento:
  cabecera `Okular::DocumentSynopsis : public QDomDocument`
  (`/usr/include/okular/core/document.h:1548`), virtual
  `Generator::generateDocumentSynopsis()` (`generator.h:361`), símbolos
  `T Okular::DocumentSynopsis::DocumentSynopsis()` @ `0xa85d0` y
  `T Okular::Generator::generateDocumentSynopsis()` @ `0xc7230` en
  `libOkular6Core.so.4.0.0`; el backend PDF lo construye (import de
  `DocumentSynopsis::DocumentSynopsis()`); UI con la cadena `Contents` en
  `okularpart.so` @ offset `104701`.
- **Estado real de Glosa.** El lector muestra una página por vez
  (`web/notes.js:456,476`) y **no** lee el índice del PDF: `getOutline()` no
  aparece en `web/` (fuera de `vendor/`). Existe ya un panel lateral llamado
  `course-outline` (`web/index.html:5,12`) pero es el índice de **lecciones** de la
  materia, no del PDF.
- **Interacción del estudiante.** Abre la lección que referencia “página 3 de la
  filmina X” (`courses/tecnologias.json`, `blocks[0].references`), ve el índice del
  PDF junto al de unidades y salta a la página exacta.
- **Adaptación mínima.** Usar `getOutline()` de pdf.js (ya vendorizado) y pintar sus
  entradas dentro del `course-outline` existente, intercaladas con las lecciones.
  Sin backend nuevo: el índice es del documento, no de Glosa.
- **Beneficio esperado (hipótesis).** Menos tiempo buscando el tema; navegación más
  directa entre unidad y página. **No** demuestra comprensión.
- **Dificultad/riesgo.** Baja/media. Riesgo: PDFs escaneados o sin outline (habrá que
  decir “documento sin índice”); numeración de página del PDF ≠ impresa
  (`docs/formato-cursos.md:17`).
- **Criterio de aceptación.** Con un PDF que tenga outline, abrir la lección que lo
  referencia, ver el índice y saltar a la página N correcta; con un PDF sin outline,
  no mostrar entradas inventadas. Probar con base temporal (patrón
  `tests/browser_pdf_layout.cjs`).

### P2 — Panel de repaso: resaltados + errores por materia y fecha de parcial  ·  [Prioridad 1]

- **Característica comprobada (Okular).** Vista de anotaciones/revisión agrupada:
  cadena `Reviews` en `okularpart.so` @ offset `232490`, clases de UI
  `DlgAnnotations`, `AnnotationModel`, `AnnotationPopup`, `RevisionPreview`
  (offset `1928416`); modelo con historial de revisión
  `Annotation::Revision`/`RevisionType` (`annotations.h:170,179`).
- **Estado real de Glosa.** Ya existen los insumos: resaltados por documento
  (`web/notes.js:439-446`, `renderAnchors` en `:409`), errores de parcial
  (`web/study-tools.js:269`; validación `library.py:306-319`), propiedades
  `materia`/`unidad`/`parcialDate` (`library.py:284-304`) y la pestaña **Parciales**
  (`web/plan.js:39-43`). Lo que **no** existe es una **vista única de repaso** que
  cruce “qué resalté/qué me equivoqué/para qué parcial”.
- **Interacción del estudiante.** En Parciales, para la materia y fecha elegidas, ve
  los resaltados con su cita y el registro de errores, y salta al fragmento exacto.
- **Adaptación mínima.** Una sección más dentro de `plan.js` (pestaña Parciales) que
  consuma datos que ya expone `window.StudyTools` (`filterNotes`,
  `getBacklinks`) y el listado de anclas del apunte; sin almacenamiento nuevo.
- **Beneficio esperado (hipótesis).** Repasar por tema en lugar de por archivo.
  Sigue siendo material propio: **no** acredita dominio (`docs/herramientas-estudio.md:104-113`).
- **Dificultad/riesgo.** Media. Riesgo: duplicar vistas ya existentes en Notas; que el
  alumno confunda “ver mis errores” con “saber el tema”.
- **Criterio de aceptación.** Elegir materia+fecha y ver, sin datos inventados, los
  resaltados y errores con enlace navegable a su origen; nota sin `parcialDate` no
  aparece con urgencia ficticia (coherente con `docs/modos-tutor.md:68-72`).

### P3 — Buscador de texto en el lector y en los apuntes  ·  [Prioridad 1]

- **Característica comprobada (Okular).** Búsqueda de texto con progreso y estado:
  `Document::searchText(int, QString const&, bool, Qt::CaseSensitivity, SearchType,
  bool, QColor const&)` @ `0x9c5b0`, `Document::continueSearch(int)` @ `0x9d860`,
  `enum SearchType`/`SearchStatus` (`document.h:613,624`),
  `TextPage::findText(...)` @ `0xeef40`, flag `TextExtraction`
  (`generator.h:197-208`); UI `Search Options` @ `1854039`, `SearchLineEdit`,
  `SearchWidget`.
- **Estado real de Glosa.** No hay búsqueda dentro del PDF; el único buscador
  (`lesson-search`) filtra **títulos** de lección (`web/app.js:618`). Tampoco hay
  búsqueda global de contenido en apuntes/lecciones.
- **Interacción del estudiante.** Busca “segunda ley” en el PDF abierto y salta a las
  coincidencias; o busca en todos sus apuntes de la materia.
- **Adaptación mínima.** (a) En el lector, extraer texto con `page.getTextContent()`
  de pdf.js y resaltar coincidencias al estilo del overlay de resaltados ya
  existente (`web/notes.js:439-446`). (b) En apuntes, reutilizar el escaneo de texto
  que ya hace `getMentions` (`web/study-tools.js:145`) para ofrecer coincidencias.
- **Beneficio esperado (hipótesis).** Encontrar referencias sin releer; menos fricción.
- **Dificultad/riesgo.** Media. Riesgo de rendimiento en documentos largos y de
  acentos/mayúsculas; nunca indexar apuntes privados fuera de lo autorizado.
- **Criterio de aceptación.** En un PDF con texto, buscar un término y saltar a la
  página correcta con la coincidencia resaltada; en un PDF escaneado sin capa de
  texto, decirlo explícitamente (no “sin resultados” silencioso).

### P4 — Marcadores de repaso con “anterior/siguiente”

- **Característica comprobada (Okular).** `BookmarkManager::addBookmark(DocumentViewport)`
  @ `0x747f0`, `nextBookmark` @ `0x78530`, `previousBookmark` @ `0x78af0`,
  `bookmarks(QUrl) const` @ `0x71b60` (`nm -DC libOkular6Core.so.4.0.0`); UI
  `Add Bookmark` @ `1850632`, `Next Bookmark` @ `1849026`; el backend PDF consulta
  `Document::bookmarkedPageList()`/`bookmarkedPageRange()`.
- **Estado real de Glosa.** Sólo se recuerda `current.page` (una página por apunte,
  `web/notes.js:7,458`). No hay lista de marcadores ni navegación entre ellos.
- **Interacción del estudiante.** Marca “acá vuelvo” en varias páginas del mismo PDF
  y salta de una a otra.
- **Adaptación mínima.** Guardar marcadores como anclas del apunte con
  `scope:'page'` y sin `quote` (el esquema ya admite anclas de página,
  `library.py:254-276`), más dos botones “◀ marcador / marcador ▶” en el lector.
- **Beneficio esperado (hipótesis).** Retomar el punto de estudio rápido.
- **Dificultad/riesgo.** Baja. Riesgo: solaparse con los resaltados (conviene
  distinguir tipo) y mantener IDs estables entre revisiones del apunte.
- **Criterio de aceptación.** Crear dos marcadores, recargar y navegar entre ellos en
  orden, sin duplicar ni perder resaltados existentes.

### P5 — Cita/ficha desde la selección del PDF

- **Característica comprobada (Okular).** Selección y texto por página:
  `TextPage::wordAt(...)` (`textpage.h:189`), `TextPage::textArea(TextSelection)`
  (`textpage.h:200`), `TextSelection` (símbolo `TextSelection::start/end`); UI
  `Select All Text on Current Page` @ `1866040`.
- **Estado real de Glosa.** La selección sólo crea un resaltado
  (`highlightSelection`, `web/notes.js:449-455`). Existe la ficha de concepto
  (`insertConceptCard`, `web/study-tools.js:370`) pero se invoca desde Notas con un
  nombre, no desde el PDF.
- **Interacción del estudiante.** Selecciona un fragmento, elige “Nueva ficha” y la
  plantilla se inserta con el texto y la fuente (“PDF X, pág. N”) ya precargados.
- **Adaptación mínima.** Agregar una acción más a `showReadingActions`
  (`web/app.js:246`) que llame a `StudyTools.insertConceptCard` y precargue
  `Fuente`. Reutiliza el guardado real del apunte (`ClassNotes.flush`).
- **Beneficio esperado (hipótesis).** Convertir lectura en material de estudio sin
  retipeo; **no** equivale a comprender (la ficha es autoevaluación).
- **Dificultad/riesgo.** Baja. Riesgo: `insertConceptCard` inserta al final de la
  nota; hay que conservar el borrador (documentado en `docs/herramientas-estudio.md:39-63`).
- **Criterio de aceptación.** Desde una selección, insertar ficha con cita exacta y
  página correcta; recargar y comprobar persistencia y que el borrador no se pierde.

### P6 — Modo continuo y franja de miniaturas

- **Característica comprobada (Okular).** Modos de vista `&Continuous` @ `1855035`,
  `&Facing Pages` @ `1855011`, `&Overview` @ `1855025`, acción
  `setContinuousMode` @ `1828864`, señal `viewContinuousChanged`; miniaturas
  `Thumbnails` @ `237111`, `ThumbnailList`, `Sync Thumbnail with Page`.
- **Estado real de Glosa.** El lector pinta **una sola página** por vez
  (`paint`, `web/notes.js:476`), sin desplazamiento continuo ni miniaturas.
- **Interacción del estudiante.** Desplazarse de corrido por el PDF y ver una tira de
  miniaturas para orientarse.
- **Adaptación mínima.** Renderizar una ventana de páginas contiguas sobre el mismo
  `pdf.js` (ya local) y una tira de miniaturas; conservar el modelo de anclas por
  página para que los resaltados sigan funcionando.
- **Beneficio esperado (hipótesis).** Lectura más fluida de material largo.
- **Dificultad/riesgo.** **Alta**: recálculo de rects de resaltados al cambiar el
  layout, memoria y rendimiento, y pruebas de posición de scroll. Es el ítem más
  costoso; conviene postergarlo.
- **Criterio de aceptación.** Leer tres páginas de corrido, con los resaltados en su
  lugar exacto, sin salto de posición al redimensionar el panel.

### P7 — Hoja de repaso exportable del parcial

- **Característica comprobada (Okular).** Exportación/impresión del documento con
  anotaciones: acción `slotExportAs` @ `170920`; impresión `Okular::FilePrinter`
  (`optionDoubleSidedPrinting`, `mediaPageSize`, `pdf2psAvailable`) y
  `GeneratorFeature { PrintNative, PrintToFile }` (`generator.h:203-205`).
- **Estado real de Glosa.** Ya exporta: apunte a Markdown (`web/notes.js:528`),
  historial JSON/Markdown (`server.py:789,792`), pliego a ZIP
  (`web/rooms.js:215`). `library.py:32-84` arma una “ficha de estudio” y
  `library.py:80-81` exporta las anclas con su cita. Lo que **no** existe es una
  **hoja consolidada por parcial** (materia + fecha) lista para imprimir o repasar.
- **Interacción del estudiante.** Pide “hoja de repaso del parcial del 30/10” y
  obtiene un Markdown/impresión con resaltados citados y errores de esa materia.
- **Adaptación mínima.** Una ruta de exportación que reúna lo que ya produce
  `study_markdown` y el listado de anclas, filtrando por `materia`/`parcialDate`.
- **Beneficio esperado (hipótesis).** Repaso fuera de la pantalla; organización, no
  aprendizaje demostrado.
- **Dificultad/riesgo.** Baja/media. Riesgo: incluir por error apuntes privados
  (respetar visibilidad, `docs/privacidad.md`) y no presentar la hoja como “nota”.
- **Criterio de aceptación.** Exportar y comprobar que sólo entran apuntes de la
  materia declarada y que las citas coinciden con el fragmento original.

---

## 3. Las tres prioridades

1. **P1 — Índice del documento anclado a unidades y lecciones.** Es el mayor
   retorno de navegación para preparar parciales con bibliografía extensa, con
   esfuerzo bajo y sin backend nuevo.
2. **P2 — Panel de repaso por materia/fecha de parcial.** Reutiliza todo lo que ya
   existe (resaltados, errores, plan) y ordena el estudio por examen, que es el
   propósito principal declarado.
3. **P3 — Búsqueda de texto en el lector y en los apuntes.** Elimina la relectura
   completa como única estrategia; habilita llegar a un concepto puntual.

Sugerencia de orden de ejecución: P1 → P3 → P2 (P1 y P3 comparten el manejo de texto
del PDF; P2 es sobre todo composición de datos ya disponibles).

## 4. Tres características que **no** trasladaría

1. **Modo presentación y transiciones de página** (`Enter Presentation Mode` @
   `1850203`, `DlgPresentation`, `PresentationWidget`, `PageTransition`). Glosa es
   estudio individual en loopback, no una herramienta para exponer; agrega UI y
   estado de ventana/segunda pantalla sin atender preparar un parcial.
2. **Firma digital y validación PGP** (`SignatureAnnotation`,
   `SignatureInfo::setSignature/setCertificateInfo`, cadenas `Enable PGP
   Signatures`, `Signature backend:`). Requiere infraestructura de confianza,
   claves y servicios externos; fuera del propósito y del modelo de costo cero.
3. **Anotaciones multimedia/embebidas** (`MovieAnnotation`, `ScreenAnnotation`,
   `WidgetAnnotation`, `RichMediaAnnotation`; `Okular::Movie::setAutoPlay`).
   Contradice la regla del proyecto de no meter componentes ejecutables en el curso
   (`docs/formato-cursos.md:3`) y amplía superficie de riesgo sin aporte al repaso.

(Otras no prioritarias, por si se preguntan: previsualización de impresión con CUPS,
gestión de formularios acroform, miniaturas–galería como fin en sí mismo.)

---

## 5. Bloqueo real de REA (diagnóstico acotado)

REA `6.4.0` (`<HOME>/.local/bin/rea`) quedó **bloqueado** para análisis de
código nativo: `rea doctor` reporta `providers: []` y motores ausentes
(hopper/ghidra/ida = `missing_analysis_engine`). Concretamente:

- `rea inspect-binary-layout <poppler.so>` → exit 1, `provider_unavailable`,
  `requested_provider_id: pwntools-elf`, exige `REA_PWNTOOLS_PYTHON` con
  pwntools/pyelftools/Unicorn; no hay `pwn` en `python3`, `python3.12` ni
  `.venv-author`.
- `rea analyze <libOkular6Core.so.4.0.0>` → exit 1, `provider_unavailable`.
- El único camino que respondió fue `rea inspect-artifact`, que devuelve inventario
  de contenedor (`node_count 1`, `edge_count 0`,
  `evidence_id ev_edc28d167959456277dabb204ea5a208641e89d123962c0a7a0b5f01e00dd9bf`),
  sin funciones ni símbolos.

Como el encargo prohíbe instalar motores y hacer setup global, **no se reparó** la
ruta (es una limitación de política, no un defecto de REA). Detalle y salidas crudas
en `evidence/rea-blocker.md`, `evidence/rea-binary-layout-poppler.json`,
`evidence/rea-analyze-core.json`.

Comprobado con otras herramientas **estáticas** (sin ejecutar nada): `file`,
`readelf -h/-d`, `nm -DC` (símbolos dinámicos), `strings -n 4`, `sha256sum`,
`pacman -Ql`, las cabeceras del paquete `/usr/include/okular/**` y los recursos
`/usr/share/okular/*.xml`.

### Estático vs. runtime, y desconocido vs. ausente

- **Estático (observado):** existencia y firma de símbolos, clases, enums, recursos
  XML y cadenas; ausencia de `getOutline` en Glosa (búsqueda sobre el árbol fuente).
- **Runtime (no observado):** no se ejecutó Okular ni Glosa; no se afirma nada sobre
  comportamiento efectivo, rendimiento ni calidad del índice/búsqueda reales.
- **Desconocido:** no pude verificar en ejecución si el backend PDF de esta versión
  concreta entrega un outline no vacío en un PDF dado, ni su calidad; la producción
  del `TextPage` sí tiene evidencia estática (imports), su calidad no.
- **Ausente (comprobado por búsqueda en el fuente de Glosa):** índice de PDF,
  marcadores múltiples, búsqueda en el lector, modo continuo/miniaturas y
  “ficha desde selección”.

---

## 6. Archivos de evidencia

```
/tmp/glosa-okular-research/
  informe-deepseek.md                 (este informe)
  task.md                             (encargo)
  evidence/
    rea-blocker.md                    diagnóstico y salidas crudas de REA
    rea-binary-layout-poppler.json    salida REA (provider_unavailable)
    rea-binary-layout-poppler.err
    rea-analyze-core.json             salida REA (provider_unavailable)
    rea-decompile-core.json           REA decompile (argumento/proveedor ausente)
    rea-inspect-artifact-poppler.json única salida REA exitosa (inventario)
    manifest-sha256.txt               hashes de toda la evidencia
    okular-features.md                evidencia estática de Okular + offsets
    glosa-state.md                    estado real de Glosa con rutas/líneas
    offsets-and-symbols.txt           offsets de cadenas y símbolos clave
    hashes.txt                        SHA-256 de artefactos y recursos
    nm-core.txt / nm-poppler.txt      símbolos dinámicos
    nm-poppler-undef.txt              imports Okular::/Poppler:: del backend PDF
    nm-core-key-symbols.txt           símbolos clave del núcleo
    strings-okularpart.txt            cadenas de la UI
    strings-poppler.txt               cadenas del backend PDF
    strings-okular-bin.txt            cadenas del lanzador
    pacman-Ql-okular.txt              contenido del paquete (1683 entradas)
    readelf-dyn-core.txt / readelf-dyn-poppler.txt
```

Toda la evidencia es reproducible con los comandos citados en cada archivo. No se
incluye ningún dato personal ni historial de usuario.
