# Investigación profunda: 58 oportunidades de mejora para Glosa

El objetivo es preparar parciales: comprender relaciones, intentar responder sin ayuda, localizar fuentes, corregir errores y repartir práctica antes del examen. Esta revisión cubre el código de Glosa y familias relevantes de Obsidian, Okular y KOReader; **no** pretende enumerar todas las funciones posibles de esas aplicaciones ni demostrar eficacia pedagógica.

Para retomar en otra conversación: [encargo listo para otro agente](ENCARGO-OTRO-AGENTE.md). Permite elegir IDs, agregar preferencias y limitar la implementación a lo seleccionado.

**Entrega principal: [inventario de las 58 funcionalidades](INVENTARIO.md)**. Tiene tabla por área y detalle por entrada: estado actual, evidencia del código, límite encontrado, propuesta, prioridad, aceptación y referencia externa cuando la hay. [Versión estructurada JSON](inventario.json).

No se implementaron funciones. No se consultaron bases ni materiales de estudio personales. No hace falta descargar nada más para reproducir los hallazgos alcanzados: se usaron programas instalados y la distribución de KOReader ya verificada.

## Conclusión de producto

La prioridad es integrar **lección → concepto/fuente → intento → evidencia por criterio → error → caso nuevo → repaso**. Muchas piezas existen; agregar otro panel independiente sin conectar ese recorrido multiplicaría lugares que administrar.

Mantener conceptos enlazados en el texto de las lecciones y consultables por preview, como pidió el estudiante. No reintroducir un glosario separado como paso obligatorio. La preview y la búsqueda de contenido de Notas ya existen; no se cuentan como nuevas funciones.

## Qué haría primero

| Orden | Entradas | Cambio concreto y motivo |
|---|---|---|
| 1 | G37 | **Reparar y completar referencias a fuentes.** Hay una incompatibilidad comprobada: `safeSourceUrl` devuelve `null` para `/documents/ID`, aunque es una ruta del contrato. Después, abrir página/cita en el lector y volver sin perder la tarea. |
| 2 | G05, G09 | **Volver al lugar exacto y navegar por marcas.** Documento+versión, página y posición relativa; párrafo de lección y borrador. Los marcadores por ubicación y el historial por recencia son cosas diferentes. |
| 3 | G14, G15, G47 | **Unificar conceptos por ID.** Los enlaces de lección ya usan IDs, pero las referencias inversas del panel siguen wikilinks por título. Desambiguar alias y autocompletar destinos sin crear copias de la definición. |
| 4 | G16, G17, G19, G24 | **Transformar fichas y errores en práctica.** Primero pedir una respuesta; después consultar explicación/fuente; tras ayuda, proponer un caso nuevo. La cola se ajusta al parcial y no se acredita por un botón «lo sabía». |
| 5 | G25, G26, G44 | **Evidencia visible por criterio y versión.** Poder ver qué respuesta acredita qué, qué se hizo con ayuda y qué quedó incierto; un cambio editorial no debe volver invisible el registro previo. No transferir dominio automáticamente a criterios cambiados. |
| 6 | G01, G39 | **Búsqueda con contexto y destino exacto.** Extender la búsqueda que ya existe, incluir texto de PDF y teoría; no exponer claves/rúbricas de ejercicios antes del intento. |
| 7 | G21, G22, G34 | **Modo simulacro.** Inicio/cierre explícitos, corrección diferida y tiempo configurable por examen. No confundir minutos de lectura, reloj visible y dominio. |
| 8 | G29–G33 | **Un siguiente paso coherente con el parcial.** Alcance confirmado, plan local/global compatibles y acción que abre la tarea concreta. No crear un tercer planificador. |

No significa implementar esas ocho líneas completas antes del próximo examen. Conviene entregar partes verificables y probarlas en un recorrido real de estudio.

## Cobertura de la lista

| Área | Contenido |
|---|---|
| PDF | Búsqueda, índice, navegación visible, continuidad, posiciones, enlaces, selección a ficha, escaneos/OCR, marcadores, accesibilidad, regiones, rotación/recorte. |
| Conceptos y apuntes | Enlaces en contexto, preview útil y táctil, IDs/wikilinks, alias, fichas activas, errores y relaciones explicadas. |
| Práctica y evaluación | Cola por criterio, retención, simulacro, tiempo, intercalación, transferencia después de ayuda, evidencia, intentos, incertidumbre y producción no textual. |
| Planificación | Temario confirmado, siguiente tarea ejecutable, políticas local/global, replanificación, calendario y formato docente. |
| Tutor | Contexto controlado, recuperación de páginas explicable, apertura de fuentes y separación consulta/evaluación. |
| Navegación y acceso | Búsqueda integrada, encabezados, atajos visibles, audio opcional y comparación de fuentes. |
| Datos y autoría | Conflictos, historial/versiones, revisión editorial, continuidad sin conexión e importación de anotaciones. |
| Edición y repaso portátil | Autocompletado, contenido referenciado, bloques de ayuda, fórmulas, notas al pie, filtros guardados, diagramas y hoja de repaso exportable. |

## Qué se consiguió efectivamente con REA

La [evidencia detallada](EVIDENCIA.md) separa qué se observó, por qué herramienta, y qué sigue siendo propuesta.

- **Okular:** Ghidra instalado se conectó por REA. Los binarios completos no terminaron de analizarse; se aisló un ELF de nueve funciones con bytes y direcciones originales verificados. REA produjo **seis dossiers nativos** con pseudocódigo, assembly y bloques de control: siguiente/anterior marcador, comparar y serializar posiciones, continuar búsqueda y saltar de página. El contexto Qt y llamadas externas quedan parcialmente desconocidos.
- **KOReader:** REA capturó **cinco ejecuciones de módulos reales** sobre agenda de vocabulario, tiempo restante, exportación Markdown, historial y presentación de resultados. Dependencias simuladas declaradas; no se ejecutó la GUI completa ni el motor nativo de búsqueda.
- **Obsidian:** REA analizó **90 funciones reales** extraídas con procedencia verificable; recuperó relaciones estáticas locales. Hay cuatro trazas, pero sin caminos terminales y con cobertura parcial: no se venden como reconstrucción de recorridos completos de usuario.

**La lista completa de mejoras no es «58 funciones extraídas con REA».** Combina evidencia REA acotada, lectura de recursos distribuidos, auditoría de Glosa y propuestas de diseño. Cada fila conserva esa distinción.

## Reservas de la revisión del coordinador

1. Se verificó la procedencia de 90 fragmentos JS y nueve fragmentos nativos. Esto confirma qué bytes se analizaron, no la corrección semántica de todos los resultados.
2. Se inspeccionaron las seis salidas de Ghidra y las cinco capturas de KOReader; las advertencias se conservan. No se confunden exit 0, cantidad de relaciones o número de funciones con cobertura total.
3. Los informes de agentes se conservan como evidencia de la delegación. Algunas expresiones sobre Obsidian son demasiado fuertes: relaciones como `reads-property`, `writes` o una semilla resuelta **no demuestran por sí solas** el significado completo de una función UX.
4. `findCurrentOutlineItem` en el corpus es de **índice PDF**; otras funciones de encabezados pueden pertenecer a clases distintas. No se infiere una cadena común solo por los nombres.
5. Los «exports default» del corpus JS son una consecuencia de los wrappers auxiliares, no los exports originales de Obsidian.
6. La discrepancia del hash de Obsidian de la pasada anterior ya fue corregida: base del ASAR `8 + segundo entero`, SHA-256 correcto de `app.js` `958ce57fe22f87fdf121546e46dfccd9c8ee971ce3fd8f801d60d4ece39a2df9`. Un informe que la sigue mencionando como desconocida queda corregido por esta revisión.
7. En el informe de KOReader, que no se haya usado Ghidra para esa pasada de Lua no significa que Ghidra no esté instalado. Se configuró en el proceso propio del análisis de Okular.
8. «Sin OCR en Glosa» no significa que haga falta OCR para todo PDF: primero detectar y explicar páginas sin texto; añadir OCR local solo si el material lo necesita. Un OCR tampoco es fuente infalible.
9. Una selección de PDF puede ya resaltarse, anotarse y consultarse. La mejora es conectar esas acciones con fichas y práctica, conservando fuente y borrador.
10. `renderSimulation` en Glosa dibuja demostraciones didácticas; no es un motor de simulacro de examen ni define un tiempo de evaluación.

## Qué dejaría después

Gráficas globales y lienzos infinitos como centro de la aplicación; rachas o volumen leído como indicador de aprendizaje; publicación/sincronización de cuentas; edición/firma avanzada de PDFs. También postergaría importar muchos formatos antes de que el recorrido básico de estudio sea consistente.

Fórmulas, diagramas, anotación de figuras y audio cambian de prioridad según materia y necesidad de acceso. No se descartan por no ser centrales para un parcial de teoría concreto.

## Entregables y comprobación

- [Inventario legible](INVENTARIO.md) y [JSON](inventario.json), 58 entradas sin IDs duplicados.
- [Auditoría de fuente de Glosa](glosa-audit.md): 46 entradas iniciales, sin datos personales ni pruebas sobre el historial real.
- Informes: [Okular](okular-informe.md), [KOReader](koreader-informe.md), [Obsidian](obsidian-informe.md).
- [Índice de evidencia y límites](EVIDENCIA.md), [manifiesto de archivos](archivos-evidencia.json).
- [Validación mecánica de procedencia y salidas](validacion.json): 126 controles, incluyendo hashes de fragmentos, existencia de dossiers/capturas y contraste de salidas de KOReader. No es una validación pedagógica independiente.
- [Probe de enlaces de fuentes](glosa-source-links-probe.json): ejecución aislada de la función de Glosa, sin base de estudiante.

Los análisis de Obsidian y KOReader se delegaron a `opencode/deepseek-v4.1-flash-free`; el coordinador hizo el análisis de Okular, la auditoría adicional y la síntesis. Las trazas de OpenCode y ensayos completos permanecen en `/tmp/glosa-deep-20261017/`; los Evidence JSON útiles están conservados aquí, comprimidos cuando son grandes. Los scripts guardados contienen rutas de esta investigación y requieren adaptarlas al reproducir en otro directorio.
