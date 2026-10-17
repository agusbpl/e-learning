# Qué aportó REA y qué no

Este índice distingue evidencia de herramienta, lectura de fuente y propuesta. Los IDs son los devueltos por REA; no se atribuyen IDs nuevos a los resúmenes del coordinador. Los JSON originales conservados se listan con hash en `archivos-evidencia.json`. Las pruebas de procedencia son controles mecánicos; no acreditan aprendizaje ni verifican eficacia pedagógica.

## KOReader: ejecución controlada de cinco módulos reales

Se ejecutó el LuaJIT empaquetado contra módulos distribuidos sin modificarlos, mediante `capture_process` de REA. El reloj, filesystem, base de datos o widgets se simulan según el harness; no se ejecutó la GUI completa ni documentos personales. Cinco capturas terminaron con exit 0 y sin truncamiento. Que el proceso termine bien no prueba por sí solo todos los contratos: se contrastaron además las salidas descritas abajo.

| Clave | Código real ejercitado | Evidence ID | Resultado y límite |
|---|---|---|---|
| KO1 | `vocabbuilder.koplugin/db.lua:gotOrForgot` | `ev_a39543fc74012390378482ed35d302c3fca58d1cb364a2ae11992398233a4a90` | Primer acierto: 1.800 s; olvido: 300 s; la racha y el intervalo cambian y el crecimiento tiene techo. DB simulada: no se comprobó la persistencia SQLite ni que una autoevaluación pruebe dominio. |
| KO2 | `readtimer.koplugin/main.lua:remaining/remainingTime` | `ev_a6b04dfb3f4fc71608088072573849159793465f047669ca30bba74c14baa8d4` | Descomposición y redondeo del tiempo restante, incluido timer no programado. Reloj simulado; no prueba alarmas ni pestañas en segundo plano. |
| KO3 | `exporter.koplugin/template/md.lua:prepareBookContent` | `ev_1a30a22265d8c7650c001923c769bb9f8f1e6cb58552ac3f2c70d2005b09d2af` | Agrupa por capítulo, conserva página/nota/estilo y crea backlink cuando se pide; datos de prueba, no exportación de una biblioteca real. |
| KO4 | `frontend/readhistory.lua:addItem/_reduce/getPreviousFile` | `ev_9261afe5a0f397756071b9165d92a764f280547997d9b93240682c444222677e` | Deduplica al reabrir, reordena por recencia, aplica un tope y representa un archivo ausente como deshabilitado. Filesystem simulado; no equivale a restaurar una posición completa en la GUI. |
| KO5 | `readersearch.lua:onShowFindAllResults` | `ev_063cb20c62a4e8ea739624b628738f7bd30e96573a0c3671a3d78f0bf1fcd64a` | Ensambla coincidencia, contexto y referencia de página sin espacios extra ante puntuación. Motor de búsqueda y documento simulados: prueba presentación de resultados, no extracción ni búsqueda nativa completa. |

Harneses, escenarios, salidas y hashes: `evidencia/koreader/`. Informe detallado: [KOReader](koreader-informe.md). Los intervalos de vocabulario no se recomiendan como política directa para un parcial inminente; la adaptación debe contemplar fecha, tiempo disponible, tipo de tarea y evidencia independiente.

## Okular: seis funciones nativas analizadas con REA + Ghidra

Se encontró Ghidra instalado y se configuró solo para los procesos de investigación. El autoanálisis de los binarios completos se interrumpió (exit 143); no se estableció definitivamente la causa de esas terminaciones. No se presenta como un éxito de análisis completo.

La recuperación fue un ELF derivado de 14.120 bytes que contiene **nueve funciones originales copiadas byte a byte**, en sus direcciones virtuales originales, con un contenedor auxiliar. REA/Ghidra completó el autoanálisis de ese fragmento y produjo seis dossiers. Se verificaron contra los offsets y hashes del binario instalado. No se ejecutó el ELF derivado.

| Clave | Función original / VA original | Evidence ID de `analyze_function` |
|---|---|---|
| OK1 | `BookmarkManager::nextBookmark` · `0x78530` | `ev_1e19c5d71b92a817e147a270fa3676184e1415878db6992a39f02cd46820997c` |
| OK2 | `BookmarkManager::previousBookmark` · `0x78af0` | `ev_b6692368f431fa2cce049decd3bb2e1ae9621a40e6bfbfb9a4b5cf44eef6c7b5` |
| OK3 | `DocumentViewport::operator<` · `0xa7ca0` | `ev_ef7fa65fedd087ab3a15c2ea68d2fae9869494c1aa2a83836c60f55cae485406` |
| OK4 | `DocumentViewport::toString` · `0xa7500` | `ev_0b38ef8390a4946813fa6a293fb64f01b70e0618d1336b576e389a6544a1b079` |
| OK5 | `Document::continueSearch(int)` · `0x9d860` | `ev_95c488b21bf45b244764ba557a47c4c509e621328616109ef534dc27c76e84ef` |
| OK6 | `Document::setViewportPage` · `0x9b1a0` | `ev_00b402497a2c49756ebca9f70d1e34dbd47734434b7f99641c54dcc7d690820c` |

Se recuperaron pseudocódigo, assembly, bloques de control y referencias. La comparación de posiciones usa un campo entero y, en condiciones determinadas, dos doubles: la cabecera distribuida los identifica como página y coordenadas normalizadas. Las funciones de marcadores recorren en sentidos opuestos y comparan con la posición actual. Continuar búsqueda opera sobre un identificador y estado, con llamadas indirectas no resueltas.

**Límite importante:** los nombres `REA_*` son auxiliares; el contenedor reducido no conserva todo Qt, imports, datos globales ni contexto. Hay advertencias de flujo truncado y tipos no recuperados. Las cabeceras ayudan a interpretar campos, pero no son tipos mágicamente recuperados por REA. No se deduce de aquí el formato completo de serialización, un contrato exacto de límites de página, navegación circular ni el comportamiento de la GUI.

Informe: [Okular](okular-informe.md). Procedencia, scripts y dossiers originales comprimidos: `evidencia/okular/`. El inventario del fragmento tiene ID `ev_dc655c41b05c0c565bae3a77b65557db610360f87b2cdcb24a2e469862015fcc`.

## Obsidian: análisis semántico estático de un corpus reducido

REA analizó **90 funciones reales** extraídas por AST del renderer, verificadas 90/90 contra rangos de bytes y hashes del original. Las funciones se envolvieron para formar unidades JS parseables; sus variables externas y el módulo original no se incluyeron. No se ejecutó Obsidian.

Evidence del corpus: `ev_87d26e1f9bf43cc1bbd70d9cefeeab65951eb808a887f49bf4ed92a3b789a3bc`.

- 90 archivos parseados, 0 fallos, 18.944 nodos AST.
- 13.037 relaciones semánticas, mayormente aliases, lecturas y capturas; solo 20 relaciones `calls`. El número agregado no es una medida de funcionalidades reconstruidas.
- Cobertura **parcial** y grafo semántico truncado. El corpus incluye 90 de las 15.442 funciones nombradas localizadas por el extractor; no cubre todos los módulos ni todo el comportamiento.

| Clave | Funciones/marcadores del corpus | Qué sostiene realmente la evidencia |
|---|---|---|
| OB-hover | `startHover`, `activateHover`, `showPreview`, `onHoverLink` | Propiedades, literales y uso de promesas dentro de funciones seleccionadas. El significado UX y su conexión completa son interpretación; no se probó una sesión de hover de Obsidian. |
| OB-enlaces | `triggerWikilink`, `openLinkText`, sugerencias/resolución | Literales `[[`/`![[`, lecturas/escrituras y relaciones locales. No se reconstruyó toda la resolución entre archivos o alias. |
| OB-embeds | `loadEmbed` | Escritura de `label/height/width` y creación de promesa. No prueba transclusión completa de una nota/sección en ejecución. |
| OB-busqueda | `updateSearch`, `getSearchCursor`, filtros/sugerencias | Llamadas y relaciones locales de propiedades/cursor. El contrato completo de operadores y búsqueda contextual sigue sin verificarse por ejecución. |
| OB-outline | `findCurrentOutlineItem` y otras funciones de esquema | Relaciones locales y rangos fuente. La función `findCurrentOutlineItem` inspeccionada corresponde al índice PDF, no a un esquema Markdown completo. No se deben conectar por sus nombres funciones de clases distintas. |
| OB-metadatos | `computeFileMetadataAsync`, frontmatter y propiedades | Escritura de metadata/tamaño/mtime/hash y timer programado/cancelado. La finalidad de agrupar ediciones es una inferencia, no una prueba de la política efectiva de actualización. |
| OB-callouts | `insertCallout` | Escrituras sobre una línea dentro de la función y marcadores estáticos complementarios de la primera pasada. No es una prueba del renderer completo de callouts. |

Cuatro trazas REA resolvieron sus semillas, pero devolvieron **cero caminos terminales** y esencialmente aristas de contención/exportación. Se conservaron para transparencia, no como prueba de rutas de usuario entre módulos:

- `loadEmbed`: `ev_2f06611ab5c75108619373f555d2762e7d0db94af0d47f41cd5e979864aaad7d`.
- `updateSearch`: `ev_92a9b970950b93ed5ee104510033408c5c143b3b5ce712c839675fe7ce140a21`.
- `startHover`: `ev_278724314d1b54e7f642e094846db186de0c3f5637efd1de8f474f8f88d18e26`.
- `findCurrentOutlineItem`: `ev_557076052e4cc16babbab7c2459728481777a0a01ca0f57a6dd1340cc1fb6e87`.

Informe original del agente: [Obsidian](obsidian-informe.md). La revisión de esta página prevalece ante formulaciones demasiado fuertes del informe. Corpus INDEX y extractor se conservan; no se copió el programa instalado al repositorio. La discrepancia anterior del hash quedó resuelta en la primera revisión: la base correcta del ASAR usa el segundo entero del header; que el informe del agente la deje como incógnita no la reabre.

## Referencias que no se presentan como extracción funcional REA

Las claves siguientes remiten a la lectura estática normal de recursos distribuidos de la primera pasada, o a una propuesta propia:

- `OTRA-indice-pdf`: símbolos/cabeceras `DocumentSynopsis` y `generateDocumentSynopsis` de Okular. No forman parte de los seis dossiers nuevos.
- `OTRA-matematica`: biblioteca MathJax empaquetada y carga referenciada en Obsidian.
- `OTRA-pies`: marcadores y recursos de notas al pie de Obsidian.
- `OTRA-etiquetas`: recursos de etiquetas; guardar vistas por dificultad es diseño para Glosa.
- `OTRA-diagramas`: Mermaid empaquetado; dibujar un diagrama no demuestra comprenderlo.
- `OTRA-regiones`: tipos/herramientas de anotación distribuidas de Okular; el flujo de selección de región propuesto no se ejecutó.
- `OTRA-sidecars`: código Lua distribuido de importación/exportación de anotaciones; no se importaron anotaciones personales ni se ejecutó ese flujo.
- `OTRA-geometria`: cabecera `Page::rotation`, `totalOrientation`, `boundingBox`; no fue decompilada la UI de esos controles.
- `PROPIA-comparacion`: propuesta a partir del flujo de Glosa; no se atribuye una vista de comparación probada a REA.

Detalles de primera pasada: [investigación anterior](../2026-10-17-lectores/README.md). Ausencia de soporte REA profundo no transforma esas referencias en falsas, pero sí cambia lo que permiten afirmar.

## Glosa: comprobación concreta adicional

La función real `safeSourceUrl` de `web/app.js` se extrajo y ejecutó aislada en Node, sin servidor ni base. `/sources/a.pdf` y HTTPS producen URL con página; `/documents/doc-1` devuelve `null`. El contrato de fuentes admite `/documents/ID`, así que hay una incompatibilidad concreta que afecta a las referencias de lecciones. Se conserva el probe y su salida. No se corrigió producto durante esta investigación.
