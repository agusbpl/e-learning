# Lectores como referencia para Glosa · revisión del 17/10/2026

Se encargaron tres investigaciones independientes a **`opencode/deepseek-v4.1-flash-free`**, mediante la CLI de OpenCode. Los tres trabajos terminaron; sus trazas no registran errores de cuota y reportan costo cero. Esto describe las ejecuciones, no garantiza disponibilidad ni cupos futuros. No fue necesario cambiar de modelo.

Cada agente cargó la skill `reverse-engineer-anything` y ejecutó operaciones REA. La revisión del coordinador comprobó muestras de evidencia y contrastó propuestas con el código actual de Glosa. No se implementaron funciones de producto durante esta investigación ni se leyeron datos de estudio personales. KOReader se descargó a `/tmp`, se verificó contra el SHA-256 oficial y no se instaló ni ejecutó.

## Prioridades revisadas

El criterio es preparar un parcial: volver a explicar, aplicar, corregir y decidir qué practicar antes de la fecha. Los beneficios son hipótesis de diseño; no se midieron mejoras de aprendizaje.

| Orden | Propuesta para Glosa | Referencia y estado actual | Adaptación y aceptación mínima |
|---|---|---|---|
| 1 | **Repaso activo de errores y conceptos pendientes, limitado por la fecha del parcial.** | KOReader programa revisiones de vocabulario (`plugins/vocabbuilder.koplugin/db.lua:219–253`). Glosa ya registra errores y `needsPractice`, pero eso no programa una práctica nueva. | Reunir pendientes por parcial; primero pedir una respuesta sin mostrar la corrección, luego permitir consultar la fuente. Tras ayuda, pedir una aplicación diferente. Una fecha vencida o un clic en «lo sabía» nunca cambia un criterio a dominio independiente. Calendario reproducible con reloj inyectable, sin copiar ciegamente intervalos de meses para un examen en días. Esfuerzo medio. |
| 2 | **Volver al mismo lugar después de consultar una nota o fuente.** | KOReader mantiene historial (`frontend/readhistory.lua`, `addItem`, `getPreviousFile`). Glosa recuerda parte del estado de cada vista y tiene previews, pero no una pila explícita de ida y vuelta con ubicación de lección, párrafo, nota y PDF. | Añadir «Volver a donde estaba» y navegación atrás/adelante; conservar desplazamiento, página y borrador al abrir un término. Aceptación: seguir dos enlaces, volver dos veces y recuperar cada ubicación sin perder texto ni alterar historial de respuestas. Esfuerzo medio. |
| 3 | **Búsqueda con fragmentos y salto al lugar exacto, incluido el PDF.** | Obsidian contiene búsqueda contextual y operadores; KOReader implementa lista de resultados y salto (`readersearch.lua:680,708,791,873`); Okular expone búsqueda en su API. Glosa ya busca dentro de notas, pero el resultado no es una aparición contextual navegable; el buscador de lecciones filtra títulos. | Primero ampliar el buscador del pliego a resultados de notas y teoría, con contexto; después añadir búsqueda textual en el PDF con pdf.js local. No revelar claves, rúbricas ni soluciones de ejercicios antes del intento. Un PDF sin texto debe explicitar esa limitación; no inventar OCR. Guardar el borrador antes de navegar. Esfuerzo medio. |
| 4 | **Convertir una selección en una pregunta o ficha con fuente preservada.** | Okular expone selección y anotaciones; KOReader conserva contexto del término y exporta anotaciones. Glosa ya tiene selección, anclas y fichas, pero esos flujos requieren pasos separados. | Desde un fragmento, ofrecer crear una ficha o pedir una pregunta con fuente, página y cita exactas. Mantener separadas la cita y la explicación propia. Crear el material no acredita aprendizaje; toda pregunta generada necesita revisión de fuente y rúbrica. Aceptación: cita y página correctas, borrador preservado y ninguna acreditación automática. Esfuerzo medio: no basta agregar un botón. |
| 5 | **Orientación dentro del material: índice del PDF y encabezados del apunte.** | Okular distribuye `DocumentSynopsis` y `generateDocumentSynopsis`; Obsidian incluye recursos de outline. Glosa tiene índice de lecciones, pero no un índice del PDF ni navegación por encabezados del apunte. | Ubicar cada índice en su lector, sin mezclar páginas del PDF con unidades del curso. Usar el índice real del documento y encabezados del Markdown; respetar bloques de código y títulos repetidos. Aceptación: salto correcto, sin encabezados ficticios cuando el PDF no trae índice. Esfuerzo bajo/medio. |
| 6 | **Simulacro con tiempo opcional y registro de lo que quedó sin responder.** | KOReader tiene temporizador (`plugins/readtimer.koplugin/main.lua`). Glosa registra tiempo aproximado de estudio y permite cursos con simulacros, pero no un cronómetro específico de examen. | Configurar tiempo de examen explícito; no deducirlo de minutos de lectura. Avisar al finalizar y conservar respuestas. Separar «sin terminar por tiempo», error conceptual y evidencia insuficiente. Pausa y recarga no duplican tiempo ni cambian el veredicto conceptual. Esfuerzo medio. |

Empezaría por **repaso activo, regreso al punto de lectura y búsqueda contextual**. La secuencia técnica puede arrancar por navegación/búsqueda si se necesita una entrega más acotada antes de diseñar la cola de práctica.

Como derivación del repaso, una **hoja exportable por parcial** con errores, preguntas pendientes y fuentes sería útil. No hace falta crear un segundo almacén ni generar un resumen que oculte las incertidumbres.

## Qué conservar de lo que Glosa ya tiene

- **Notas de conceptos y previews dentro de la explicación.** La propuesta de KOReader P4 de un glosario consolidado separado no se adopta: contradice la preferencia explícita del usuario. Puede reutilizarse el contexto del término para mejorar su nota nativa existente.
- **Referencias, fichas, registro de errores y propiedades** ya existen en Notas. La mejora principal es conectarlas con la lección y el repaso del parcial, no volver a implementarlas.
- **Búsqueda de notas** ya incluye título, contenido y notas por página (`web/notes.js:320`). La ampliación es contexto, destino preciso y otros tipos de material; no «agregar búsqueda desde cero».
- **Tiempo y autoevaluación** son datos útiles de organización. No equivalen a una respuesta independiente correcta ni a dominio de todos los criterios.

## Correcciones y reservas sobre los informes de DeepSeek

Los informes originales se conservan como resultados de la delegación. Esta síntesis tiene precedencia para las recomendaciones finales.

1. **Hash de Obsidian resuelto.** El agente señaló una discrepancia real con la referencia anterior del coordinador. Se verificó el header del ASAR: base `8 + header_size` (segundo entero), no `8 + pickle_size` (tercero). La extracción anterior comenzaba cuatro bytes antes. El hash correcto de `app.js` es `958ce57fe22f87fdf121546e46dfccd9c8ee971ce3fd8f801d60d4ece39a2df9`. Se corrigió `docs/obsidian-note-preview.md`. Las posiciones absolutas y las observaciones de diseño se mantienen.
2. **Glosa tiene búsqueda de contenido en Notas.** Algunas frases del informe de Okular son demasiado amplias al afirmar que no hay búsqueda de contenido. KOReader y Obsidian identifican correctamente la búsqueda existente; se confirmó en el código.
3. **`renderSimulation` no es el motor de simulacros de examen.** En `web/app.js` esa función dibuja demostraciones de integración y tableros. No debe usarse como prueba de un cronómetro de parcial; `l.minutes` tampoco define necesariamente duración de examen.
4. **Ficha desde selección requiere trabajo de integración.** Hay una acción de anotación contextual en PDF además del resaltado (`ClassNotes.annotate`). Agregar una ficha no debe duplicar ese flujo ni sobrescribir el apunte abierto. Se ajusta el esfuerzo de «bajo» a «medio».
5. **La cola es una adaptación propia.** KOReader aporta programación de vocabulario y botones de autoevaluación, no evidencia de un sistema de dominio conceptual para parciales. No se trasladan esas marcas a `assessment`.
6. **Callouts, aliases, etiquetas, fórmulas y transclusiones** pueden ser útiles, pero tienen prioridad dependiente de la materia. Para matemática, fórmulas locales podrían subir mucho de prioridad. No se concluye que todo eso haga falta antes del repaso activo.
7. **No hay mediciones de usuarios o aprendizaje.** Ninguna prioridad se apoya en un ensayo de eficacia. Tampoco se probó la interfaz de las aplicaciones en ejecución en esta investigación. La presencia de cadenas de UI es evidencia más débil que una ruta de implementación o un escenario observado.
8. **Privacidad y exportación.** Una nota propia privada puede formar parte de un repaso local si el estudiante la selecciona; «privada» no significa invisible para su dueño. La exportación y el envío al tutor deben conservar sus límites explícitos.

## Qué no trasladaría ahora

- Una gráfica global o un lienzo infinito como centro de la aplicación. Si se necesita explicar relaciones, una actividad concreta con criterios resulta una propuesta más acotada que añadir un espacio general de organización.
- Rachas, páginas leídas o tiempo visible como puntaje de aprendizaje. Pueden mostrarse como esfuerzo, sin reemplazar la evidencia de respuestas.
- Publicación, sincronización de cuentas, administración de biblioteca por cantidad, firma digital y edición avanzada de PDF. No son prioridades del encargo actual.

Esto no declara que esas funciones sean inútiles en general: quedan fuera de la prioridad elegida para Glosa.

## Evidencia y límites de REA

- **Obsidian:** REA produjo un análisis parcial del renderer (`ev_666da72795dc1cd5730926fb3d660c498b45759f4917064530c93b5c01a9dceb`) y uno completo del pequeño shell `app.asar` (`ev_59d450728ffd97f380c2653460c60b1f4b34d7abd0fe0eb85e9975121aa0d053`). El segundo no demuestra todas las funciones del renderer. Se complementó con extracción estática de recursos del ASAR.
- **Okular:** REA hizo inventario del artefacto (`ev_edc28d167959456277dabb204ea5a208641e89d123962c0a7a0b5f01e00dd9bf`), pero faltan proveedores para análisis nativo profundo. Las funciones propuestas se sustentan en símbolos, cabeceras y recursos distribuidos, no en una decompilación exitosa.
- **KOReader:** REA identificó binarios ELF; el contenedor `.tar.xz` y el análisis nativo profundo encontraron limitaciones. La evidencia funcional procede de recursos Lua distribuidos del paquete oficial. Su hash coincide con el digest oficial: `299aadb28147a25e9432ced1214ea444a4184393b5ae97cf42402c8a61b1a1b0`.
- No se ejecutaron Obsidian, Okular ni KOReader. El comportamiento efectivo, rendimiento y utilidad para el estudiante siguen sin verificarse.

## Entregables y procedencia

- [Informe de Obsidian](obsidian-deepseek.md), [informe de Okular](okular-deepseek.md), [informe de KOReader](koreader-deepseek.md).
- [Registro de modelo, sesiones y ejecución](ejecuciones.json). 42, 46 y 42 pasos reportados respectivamente; costo reportado cero en los tres, sin errores de cuota registrados. No es una garantía sobre la política del proveedor.
- Encargos originales: `obsidian-encargo.md`, `okular-encargo.md`, `koreader-encargo.md`.
- Evidencia pequeña conservada en `evidencia/`. Las trazas completas y los paquetes extraídos están en `/tmp/glosa-{obsidian,okular,koreader}-research/`, según el manifiesto. Los inventarios de hashes conservan las rutas originales de esas ejecuciones.
- Descarga oficial de KOReader: <https://github.com/koreader/koreader/releases/tag/v2026.07.1>.

La revisión del coordinador comprobó hashes y muestras de funciones de KOReader, cabeceras de Okular y el código de búsqueda, navegación, selección y simulaciones de Glosa. No ejecutó pruebas de aprendizaje ni atribuye independencia de evaluación pedagógica a otra instancia de un LLM.
