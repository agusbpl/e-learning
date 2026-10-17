# Inventario completo de esta revisión: 58 oportunidades para Glosa

Alcance: lectura, notas, práctica, evaluación, planificación, tutor, navegación y persistencia. Estado verificado en fuente, salvo prueba aislada de G37; no se ejecutaron las interfaces completas de las aplicaciones. `ausente` significa no encontrado en las rutas revisadas. Las referencias de programas externos son apoyo de diseño; las adaptaciones y beneficios son propuestas.

P0 = próxima iteración de estudio/evidencia; P1 = integración y uso; P2 = ampliación posterior. No son compromisos de fecha. Véanse [síntesis y límites de evidencia](README.md) y [índice de evidencia](EVIDENCIA.md).

## PDF

| ID | Funcionalidad | Estado | Prioridad | Cambio propuesto |
|---|---|---|---|---|
| G01 | Buscar texto dentro del PDF | ausente | P0 | Buscar frase y términos con resultados por página, contexto y navegación anterior/siguiente. |
| G02 | Índice jerárquico del documento | ausente | P1 | Mostrar índice nativo del PDF; usar índice manual claramente identificado cuando no exista. |
| G03 | Navegación de páginas visible | parcial | P1 | Añadir salto visible por número, anterior/siguiente y etiquetas de página si el PDF las tiene. |
| G04 | Continuidad entre páginas | parcial | P2 | Ofrecer desplazamiento continuo con renderizado acotado y conservar modo página. |
| G05 | Volver al lugar exacto | parcial | P0 | Historial de ubicaciones con página, desplazamiento, bloque y selección/borrador. |
| G06 | Enlaces internos y externos del PDF | ausente | P1 | Renderizar enlaces del PDF, destinos internos y política segura para externos. |
| G07 | Selección a pregunta o ficha | parcial | P0 | Crear una ficha/pregunta desde la selección con cita, hash, página y enlace de regreso. |
| G08 | Lectura de escaneos | parcial | P1 | Detectar páginas sin texto y ofrecer OCR local opcional conservando original y procedencia. |
| G09 | Marcadores de lectura | ausente | P2 | Guardar marcadores nombrados por documento y recuperarlos desde la lección. |
| G10 | Accesibilidad del contenido PDF | parcial | P1 | Vista de texto accesible por página con encabezados cuando existan y navegación de lectura. |
| G55 | Anotar regiones, tablas y esquemas | parcial | P1 | Seleccionar una figura o celda de tabla con referencia a página/rectángulo, explicación propia y enlace al original. |
| G58 | Rotación y recorte visual por documento | parcial | P2 | Rotación y márgenes visuales reversibles para tablas o filminas, conservando coordenadas del PDF original. |

## Notas y conceptos

| ID | Funcionalidad | Estado | Prioridad | Cambio propuesto |
|---|---|---|---|---|
| G11 | Conceptos enlazados en la lección | existe | P0 | Añadir revisión editorial de términos relevantes sin links y selector de nota durante autoría; mantener texto natural. |
| G12 | Preview contextual del concepto | existe | P1 | Conservar preview y permitir resumen/acepción pertinente, fuente y expandir contenido largo. |
| G13 | Consulta de conceptos en táctil | parcial | P1 | Ofrecer acción táctil para preview y otra para abrir sin perder ubicación. |
| G14 | Unificar enlaces por ID y wikilinks | parcial | P0 | Resolver ambas sintaxis a identidad de nota y mostrar backlinks también desde bloques de curso. |
| G15 | Ambigüedad y alias de conceptos | parcial | P1 | Alias y selector de destino cuando coinciden títulos; no enlazar automáticamente homónimos. |
| G16 | Ficha como práctica recuperable | parcial | P0 | Permitir responder pregunta de ficha ocultando definición y registrar intento ligado a criterio explícito. |
| G17 | Registro de errores y reintento | parcial | P0 | Enlazar error con ejercicio, criterio y fuente; generar caso nuevo para comprobar resolución. |
| G18 | Conceptos con relaciones explicadas | parcial | P2 | Relaciones pequeñas como se diferencia de, requiere, aplica a con explicación y fuente dentro de notas. |

## Práctica y evaluación

| ID | Funcionalidad | Estado | Prioridad | Cambio propuesto |
|---|---|---|---|---|
| G19 | Cola de repaso por criterio | parcial | P0 | Construir cola de criterios pendientes y frágiles, ordenada por parcial y evidencia independiente. |
| G20 | Retención después de acreditar | parcial | P0 | Agendar comprobaciones espaciadas de recuperación con plazos explícitos y posibilidad de ajustar. |
| G21 | Simulacro con corrección diferida | ausente | P0 | Sesión de simulacro que fije preguntas y orden y revele correcciones al terminar. |
| G22 | Tiempo de simulacro | parcial | P1 | Cronómetro opcional con pausa e interrupciones diferenciadas; distinguir inconcluso de error conceptual. |
| G23 | Intercalación de unidades | parcial | P0 | Sesiones mixtas por alcance confirmado y criterios, con selección trazable y azar del sistema cuando corresponda. |
| G24 | Reformular casos después de ayuda | parcial | P0 | Acción explícita Pedir comprobación nueva ligada al criterio, con versión y fuente verificadas. |
| G25 | Tablero de evidencia por criterio | parcial | P0 | Mostrar criterio, cita del estudiante, estado, independencia, fecha y próxima comprobación. |
| G26 | Historial comparativo de intentos | parcial | P1 | Comparar intentos de un mismo criterio y separar qué cambió tras explicación o transferencia. |
| G27 | Incertidumbre y reclamo de evaluación | parcial | P1 | Acción revisar criterio que adjunte respuesta, rúbrica y fuente y deje auditoría de reevaluación. |
| G28 | Práctica de producción no textual | parcial | P2 | Adjuntar desarrollo, esquema o imagen para materias que lo requieran; criterios que evalúen su contenido. |

## Planificación

| ID | Funcionalidad | Estado | Prioridad | Cambio propuesto |
|---|---|---|---|---|
| G29 | Alcance confirmado del parcial | existe | P0 | Integrar selección y confirmación de unidades/notas al evento de parcial desde UI. |
| G30 | Plan global y siguiente acción ejecutable | parcial | P0 | Cada tarea debe abrir lección, fuente o comprobación concreta y volver al plan. |
| G31 | Dos planificadores coherentes | parcial | P0 | Alinear motivo de siguiente tarea entre Hoy, recomendación de curso y Parciales, mostrando conflictos explícitos. |
| G32 | Presupuesto y replanificación por hechos | parcial | P1 | Replanificar por tareas realizadas/evidencia y disponibilidad corregida, con vista previa de qué queda afuera. |
| G33 | Eventos globales editables | parcial | P1 | Calendario conjunto con filtro por materia/pliego y detección de compromisos superpuestos. |
| G34 | Preparación según formato docente | parcial | P1 | Registrar formato declarado, duración, recursos permitidos y tipos de desempeño esperados con fuente. |

## Tutor y contexto

| ID | Funcionalidad | Estado | Prioridad | Cambio propuesto |
|---|---|---|---|---|
| G35 | Contexto controlado por el estudiante | existe | P1 | Presets por parcial o tarea que muestren selección efectiva y advertencias de presupuesto antes de preguntar, conservando el bloqueo explícito sin truncamiento silencioso. |
| G36 | Búsqueda contextual explicable | parcial | P1 | Mostrar fragmentos recuperados, permitir fijar/descartar y ampliar consulta con sinónimos editables. |
| G37 | Abrir la fuente de una explicación | parcial | P0 | Corregir resolución de fuentes registradas y abrir citas en el lector integrado con regreso al chat/lección. |
| G38 | Separar consulta de evaluación | parcial | P0 | Acciones claras explicar duda, guardar intento y evaluar evidencia, manteniendo registro de ayudas. |

## Navegación y accesibilidad

| ID | Funcionalidad | Estado | Prioridad | Cambio propuesto |
|---|---|---|---|---|
| G39 | Búsqueda unificada de estudio | parcial | P0 | Una búsqueda por concepto con resultados etiquetados en bloques, notas, PDFs, errores y ejercicios del alcance. |
| G40 | Índice de encabezados de nota | parcial | P1 | Índice plegable de encabezados de la nota y páginas con marcas y dudas. |
| G41 | Atajos descubribles y perfil estándar | existe | P1 | Paleta contextual por vista y ayudas breves junto a acciones relevantes, con controles visibles equivalentes. |
| G42 | Audio de lectura como apoyo | ausente | P2 | Lectura opcional desde selección, velocidad y pausa con proveedor/costo explícito y sincronización limitada. |
| G56 | Comparar fuentes en vistas fijadas | parcial | P2 | Fijar dos referencias sin perder la lección; permitir anotar qué coincide, qué difiere y qué queda incierto. |

## Persistencia y autoría

| ID | Funcionalidad | Estado | Prioridad | Cambio propuesto |
|---|---|---|---|---|
| G43 | Recuperación de conflictos comprensible | parcial | P1 | Interfaz para comparar local/servidor/archivo y elegir o fusionar sin perder ninguna versión. |
| G44 | Versionar sin ocultar evidencia anterior | parcial | P0 | Relacionar criterios estables entre versiones y mostrar evidencia histórica pendiente de revalidar, sin acreditarla automáticamente. Diferenciar cambio editorial de cambio conceptual, mantener visible evidencia previa con su versión y exigir revisión antes de transferirla a un criterio nuevo. |
| G45 | Previsualización y revisión semántica editorial | parcial | P0 | Informe revisable de cambios, fuentes, enlaces rotos y criterios afectados antes de activar versión. |
| G46 | Uso sin conexión y continuidad móvil | parcial | P2 | Definir modo desconectado explícito para lecturas seleccionadas y cola local de operaciones con resolución de conflictos. |
| G57 | Importar anotaciones de otros lectores con procedencia | ausente | P2 | Importación explícita con vista previa, hash del documento, mapeo de página/posición y separación entre cita, comentario e inferencia. |

## Edición y material

| ID | Funcionalidad | Estado | Prioridad | Cambio propuesto |
|---|---|---|---|---|
| G47 | Autocompletar enlaces y destinos | ausente | P1 | Elegir concepto/destino mientras se escribe, con ID estable y texto natural en la lección. |
| G48 | Incrustar una definición o sección sin duplicarla | ausente | P2 | Referencia en solo lectura a una sección de una nota, indicando origen y versión; ciclos y límites explícitos. |
| G49 | Bloques de ejemplo, advertencia y ayuda plegable | ausente | P1 | Bloques con etiqueta semántica y plegado opcional para ayuda/solución, sin adelantar respuestas durante un intento. |
| G50 | Fórmulas matemáticas legibles | ausente | P1 | Notación matemática local en lecciones, notas y previews; conservar código editable, accesibilidad y exportación. |
| G51 | Notas al pie y citas bidireccionales | ausente | P1 | Cita breve en el párrafo, fuente en nota al pie y retorno al marcador; no sustituir documento/página por texto sin trazabilidad. |
| G52 | Etiquetas y vistas de repaso guardadas | parcial | P2 | Guardar búsquedas/filtros como «errores de unidades» o «argumentación pendiente», con alcance visible por parcial. |
| G53 | Diagramas para explicar procesos y relaciones | ausente | P2 | Diagramas locales editables de procesos/arquitecturas, acompañados de una consigna para explicar relaciones y límites. |

## Repaso portátil

| ID | Funcionalidad | Estado | Prioridad | Cambio propuesto |
|---|---|---|---|---|
| G54 | Hoja de repaso por parcial exportable | parcial | P1 | Exportar errores, dudas, fichas, preguntas pendientes y fuentes elegidos por materia/parcial; decidir si incluir respuestas aparte. |

## Detalle verificable por funcionalidad

### G01 · Buscar texto dentro del PDF

Estado: **ausente**. Prioridad: **P0**.

**Base de Glosa:** `web/notes.js:267`, `web/notes.js:476`, `tutor_context.py:114`.

**Límite encontrado:** El selector busca títulos; paint carga texto de una página. Hay recuperación textual para el tutor, no una interfaz de coincidencias del lector.

**Cambio:** Buscar frase y términos con resultados por página, contexto y navegación anterior/siguiente.

**Aceptación:** Una consulta encuentra coincidencias de varias páginas y cada resultado abre y señala el fragmento.

**Referencia externa:** KO5, OK5; consultar alcance en EVIDENCIA.md.

### G02 · Índice jerárquico del documento

Estado: **ausente**. Prioridad: **P1**.

**Base de Glosa:** `web/notes.js:458`, `web/notes.js:476`.

**Límite encontrado:** La ruta de carga/render inspeccionada no solicita getOutline.

**Cambio:** Mostrar índice nativo del PDF; usar índice manual claramente identificado cuando no exista.

**Aceptación:** Elegir una sección abre su destino; un documento sin índice no muestra un índice inventado.

**Referencia externa:** OB-outline, OTRA-indice-pdf; consultar alcance en EVIDENCIA.md.

### G03 · Navegación de páginas visible

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `web/notes.js:456`, `web/notes.js:493`.

**Límite encontrado:** El contador existe, pero pdf-page es un input hidden y el avance depende de comandos.

**Cambio:** Añadir salto visible por número, anterior/siguiente y etiquetas de página si el PDF las tiene.

**Aceptación:** Se puede saltar a página válida sin conocer atajos; se distingue página PDF de numeración impresa.

**Referencia externa:** OK6; consultar alcance en EVIDENCIA.md.

### G04 · Continuidad entre páginas

Estado: **parcial**. Prioridad: **P2**.

**Base de Glosa:** `web/notes.js:275`, `web/notes.js:476`.

**Límite encontrado:** El lector dibuja una sola página; readStep cambia al llegar al borde.

**Cambio:** Ofrecer desplazamiento continuo con renderizado acotado y conservar modo página.

**Aceptación:** El scroll atraviesa tres páginas sin vacíos ni crecimiento de canvases ilimitado.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G05 · Volver al lugar exacto

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/notes.js:458`, `web/notes.js:476`, `web/notes.js:253`.

**Límite encontrado:** Se conserva página y paint permite preservar proporción al zoom; el salto de nota no implementa una pila general de retornos.

**Cambio:** Historial de ubicaciones con página, desplazamiento, bloque y selección/borrador.

**Aceptación:** Abrir nota desde una lección y volver restaura párrafo y borrador; navegar por fuente restaura desplazamiento PDF.

**Referencia externa:** OK3, OK4, KO4; consultar alcance en EVIDENCIA.md.

### G06 · Enlaces internos y externos del PDF

Estado: **ausente**. Prioridad: **P1**.

**Base de Glosa:** `web/notes.js:476`.

**Límite encontrado:** paint crea canvas y TextLayer, sin AnnotationLayer ni resolución de destinos en la ruta inspeccionada.

**Cambio:** Renderizar enlaces del PDF, destinos internos y política segura para externos.

**Aceptación:** Un enlace de índice y una referencia interna abren el destino correcto; un enlace externo se identifica.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G07 · Selección a pregunta o ficha

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/notes.js:449`, `web/notes.js:500`, `web/study-tools.js:173`.

**Límite encontrado:** Se puede resaltar, comentar y consultar; la ficha se inserta aparte como plantilla.

**Cambio:** Crear una ficha/pregunta desde la selección con cita, hash, página y enlace de regreso.

**Aceptación:** La pregunta conserva la cita y localización y no registra dominio por crear la ficha.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G08 · Lectura de escaneos

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `library.py:194`, `web/notes.js:476`.

**Límite encontrado:** Hay extracción y TextLayer; en estas rutas no hay flujo de OCR ni advertencia específica por página sin texto.

**Cambio:** Detectar páginas sin texto y ofrecer OCR local opcional conservando original y procedencia.

**Aceptación:** Un escaneo informa que no tiene texto; el texto OCR se etiqueta y se puede corregir sin reemplazar el PDF.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G09 · Marcadores de lectura

Estado: **ausente**. Prioridad: **P2**.

**Base de Glosa:** `web/notes.js:409`, `web/notes.js:493`.

**Límite encontrado:** Hay anclas de anotación y página actual; no hay lista dedicada de marcadores sin comentario.

**Cambio:** Guardar marcadores nombrados por documento y recuperarlos desde la lección.

**Aceptación:** Se marca una página sin escribir comentario y se recupera tras recargar.

**Referencia externa:** OK1, OK2; consultar alcance en EVIDENCIA.md.

### G10 · Accesibilidad del contenido PDF

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `web/notes.js:476`.

**Límite encontrado:** Canvas tiene aria-label y existe TextLayer; esta ruta no crea árbol estructural del documento.

**Cambio:** Vista de texto accesible por página con encabezados cuando existan y navegación de lectura.

**Aceptación:** Un lector de pantalla recorre el contenido sin depender de coordenadas ni del canvas.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G11 · Conceptos enlazados en la lección

Estado: **existe**. Prioridad: **P0**.

**Base de Glosa:** `web/app.js:185`, `web/app.js:230`, `author_mcp.py:279`.

**Límite encontrado:** Existe enlace nativo estable y render compatible con resaltados; la autoría debe insertar los enlaces.

**Cambio:** Añadir revisión editorial de términos relevantes sin links y selector de nota durante autoría; mantener texto natural.

**Aceptación:** Los términos se consultan dentro del párrafo; nunca se agrega un glosario previo obligatorio.

**Referencia externa:** OB-enlaces; consultar alcance en EVIDENCIA.md.

### G12 · Preview contextual del concepto

Estado: **existe**. Prioridad: **P1**.

**Base de Glosa:** `web/app.js:191`.

**Límite encontrado:** La preview renderiza note.content completo; omite pageNotes y no contextualiza la acepción por lección.

**Cambio:** Conservar preview y permitir resumen/acepción pertinente, fuente y expandir contenido largo.

**Aceptación:** Un concepto largo muestra una definición útil sin desbordar; sigue funcionando foco y Escape.

**Referencia externa:** OB-hover; consultar alcance en EVIDENCIA.md.

### G13 · Consulta de conceptos en táctil

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `web/app.js:211`, `web/app.js:213`.

**Límite encontrado:** pointerover ignora touch y el clic navega directamente a la nota.

**Cambio:** Ofrecer acción táctil para preview y otra para abrir sin perder ubicación.

**Aceptación:** Un usuario táctil puede leer definición y cerrar manteniendo la lección en el mismo lugar.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G14 · Unificar enlaces por ID y wikilinks

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/app.js:185`, `web/study-tools.js:105`, `web/study-tools.js:132`.

**Límite encontrado:** Los enlaces nativos son por ID; referencias inversas de StudyTools siguen títulos exactos de wikilinks.

**Cambio:** Resolver ambas sintaxis a identidad de nota y mostrar backlinks también desde bloques de curso.

**Aceptación:** Renombrar una nota no rompe referencias resueltas y un link nativo de lección aparece en sus backlinks.

**Referencia externa:** OB-enlaces; consultar alcance en EVIDENCIA.md.

### G15 · Ambigüedad y alias de conceptos

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `web/study-tools.js:105`, `web/study-tools.js:138`.

**Límite encontrado:** La resolución documentada usa título exacto normalizado; no hay selección por materia o acepción.

**Cambio:** Alias y selector de destino cuando coinciden títulos; no enlazar automáticamente homónimos.

**Aceptación:** SI puede resolver a una nota elegida y dos conceptos iguales de materias distintas no se confunden.

**Referencia externa:** OB-enlaces; consultar alcance en EVIDENCIA.md.

### G16 · Ficha como práctica recuperable

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/study-tools.js:173`, `web/study-tools.js:373`.

**Límite encontrado:** La ficha es texto añadido al final de una nota, no una actividad con intento independiente.

**Cambio:** Permitir responder pregunta de ficha ocultando definición y registrar intento ligado a criterio explícito.

**Aceptación:** Se puede responder antes de ver el contenido y la evaluación no confunde rellenar plantilla con evidencia.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G17 · Registro de errores y reintento

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/study-tools.js:271`, `web/study-tools.js:542`.

**Límite encontrado:** Registro personal y corrección existen separados de los intentos y evaluaciones.

**Cambio:** Enlazar error con ejercicio, criterio y fuente; generar caso nuevo para comprobar resolución.

**Aceptación:** Un error sigue pendiente hasta una comprobación nueva; su corrección previa no se muestra antes del intento.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G18 · Conceptos con relaciones explicadas

Estado: **parcial**. Prioridad: **P2**.

**Base de Glosa:** `web/study-tools.js:132`, `web/study-tools.js:144`.

**Límite encontrado:** Backlinks y menciones indican conexión textual, sin relación conceptual tipada.

**Cambio:** Relaciones pequeñas como se diferencia de, requiere, aplica a con explicación y fuente dentro de notas.

**Aceptación:** Una comparación abre ambos conceptos y conserva su justificación; no depende de un grafo global.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G19 · Cola de repaso por criterio

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `server.py:334`, `tutor_mcp.py:386`.

**Límite encontrado:** La recomendación principal agrega por lección; sí hay criterionChecks en evaluación.

**Cambio:** Construir cola de criterios pendientes y frágiles, ordenada por parcial y evidencia independiente.

**Aceptación:** Dos criterios con estados distintos generan tareas distintas sin trasladar dominio entre ellos.

**Referencia externa:** KO1; consultar alcance en EVIDENCIA.md.

### G20 · Retención después de acreditar

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `server.py:350`, `tutor_modes.py:372`.

**Límite encontrado:** recommend omite lecciones independent; el caso todas acreditadas solo recomienda repaso integrador.

**Cambio:** Agendar comprobaciones espaciadas de recuperación con plazos explícitos y posibilidad de ajustar.

**Aceptación:** Una lección acreditada reaparece para comprobación sin borrar su evidencia previa ni inventar olvido medido.

**Referencia externa:** KO1; consultar alcance en EVIDENCIA.md.

### G21 · Simulacro con corrección diferida

Estado: **ausente**. Prioridad: **P0**.

**Base de Glosa:** `web/app.js:316`, `web/app.js:355`.

**Límite encontrado:** saveAnswer revela feedback choice antes de terminar el flujo de consulta; no hay objeto sesión de examen en esta ruta.

**Cambio:** Sesión de simulacro que fije preguntas y orden y revele correcciones al terminar.

**Aceptación:** No se ve clave durante el intento y al terminar se conserva respuesta original, orden, ayudas y feedback.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G22 · Tiempo de simulacro

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `web/app.js:546`, `web/app.js:620`.

**Límite encontrado:** Existe tiempo estimado de estudio/sesión visible; no es un cronómetro por intento de simulacro.

**Cambio:** Cronómetro opcional con pausa e interrupciones diferenciadas; distinguir inconcluso de error conceptual.

**Aceptación:** El vencimiento no convierte automáticamente una respuesta incompleta en falta de comprensión.

**Referencia externa:** KO2; consultar alcance en EVIDENCIA.md.

### G23 · Intercalación de unidades

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/app.js:162`, `server.py:334`.

**Límite encontrado:** Actividades se presentan según secuencia de una lección y recomendación elige una lección.

**Cambio:** Sesiones mixtas por alcance confirmado y criterios, con selección trazable y azar del sistema cuando corresponda.

**Aceptación:** Una sesión combina unidades incluidas sin sumar temario externo ni repetir la misma clave revelada.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G24 · Reformular casos después de ayuda

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `tutor_mcp.py:386`, `docs/evaluacion-rigurosa.md:28`.

**Límite encontrado:** La regla exige aplicación nueva; el formulario conserva el mismo ejercicio y prior response.

**Cambio:** Acción explícita Pedir comprobación nueva ligada al criterio, con versión y fuente verificadas.

**Aceptación:** Después de ayuda se evalúa un caso distinto y se identifica la respuesta como independiente o asistida.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G25 · Tablero de evidencia por criterio

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/app.js:432`, `tutor_mcp.py:386`.

**Límite encontrado:** Hay detalles de contexto y evidencia y estado de lección; falta una vista transversal estructurada por criterio.

**Cambio:** Mostrar criterio, cita del estudiante, estado, independencia, fecha y próxima comprobación.

**Aceptación:** Cada estado visible se puede rastrear a ejercicio, respuesta y cita real sin mostrar una nota numérica ficticia.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G26 · Historial comparativo de intentos

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `web/app.js:319`, `web/app.js:468`.

**Límite encontrado:** Se guardan respuestas en eventos y se muestra la última en formulario/cuaderno; no hay comparación dirigida por criterio.

**Cambio:** Comparar intentos de un mismo criterio y separar qué cambió tras explicación o transferencia.

**Aceptación:** El usuario ve ambas respuestas originales y las ayudas intermedias sin sobrescribir historial.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G27 · Incertidumbre y reclamo de evaluación

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `tutor_mcp.py:386`, `docs/evaluacion-rigurosa.md:27`.

**Límite encontrado:** El contrato admite estados de criterio inciertos y reglas; el flujo de apelación no está en la UI inspeccionada.

**Cambio:** Acción revisar criterio que adjunte respuesta, rúbrica y fuente y deje auditoría de reevaluación.

**Aceptación:** Una reevaluación conserva el dictamen previo y explica cambio o incertidumbre con fuentes.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G28 · Práctica de producción no textual

Estado: **parcial**. Prioridad: **P2**.

**Base de Glosa:** `web/app.js:316`, `server.py:133`.

**Límite encontrado:** La UI de ejercicio admite choice y textarea de explicación/aplicación.

**Cambio:** Adjuntar desarrollo, esquema o imagen para materias que lo requieran; criterios que evalúen su contenido.

**Aceptación:** Un procedimiento manuscrito se conserva como evidencia y el tutor explicita límites de lectura de la imagen.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G29 · Alcance confirmado del parcial

Estado: **existe**. Prioridad: **P0**.

**Base de Glosa:** `author_mcp.py:386`, `tutor_mcp.py:620`, `tutor_modes.py:357`.

**Límite encontrado:** Existe propuesta/confirmación de temario; el calendario local crea eventos sin seleccionar alcance en el formulario.

**Cambio:** Integrar selección y confirmación de unidades/notas al evento de parcial desde UI.

**Aceptación:** Un parcial tiene alcance visible con procedencia y estado confirmado o propuesto antes de planificar.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G30 · Plan global y siguiente acción ejecutable

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/tutor-modes.js:87`, `tutor_modes.py:488`.

**Límite encontrado:** El plan global lista cobertura y postergación; planRow muestra títulos como texto.

**Cambio:** Cada tarea debe abrir lección, fuente o comprobación concreta y volver al plan.

**Aceptación:** Desde una prioridad global se abre la tarea exacta del pliego correcto con un clic.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G31 · Dos planificadores coherentes

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `server.py:334`, `tutor_modes.py:488`, `web/plan.js:35`.

**Límite encontrado:** Conviven recomendación local y asignación global con modelos diferentes de selección.

**Cambio:** Alinear motivo de siguiente tarea entre Hoy, recomendación de curso y Parciales, mostrando conflictos explícitos.

**Aceptación:** La tarea recomendada indica si corresponde al curso o al plan global y explica cualquier diferencia.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G32 · Presupuesto y replanificación por hechos

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `server.py:317`, `tutor_modes.py:445`.

**Límite encontrado:** Existen disponibilidades, asignación y tiempos; duración no acredita dominio.

**Cambio:** Replanificar por tareas realizadas/evidencia y disponibilidad corregida, con vista previa de qué queda afuera.

**Aceptación:** Una sesión corta no marca dominio y el cambio de disponibilidad muestra tareas postergadas antes de aplicarse.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G33 · Eventos globales editables

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `web/plan.js:8`, `web/plan.js:56`, `author_mcp.py:369`.

**Límite encontrado:** El calendario por fecha filtra curso; hay vista global de parciales.

**Cambio:** Calendario conjunto con filtro por materia/pliego y detección de compromisos superpuestos.

**Aceptación:** Dos parciales de distintos pliegos aparecen juntos sin duplicar eventos ni inventar horarios.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G34 · Preparación según formato docente

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `web/app.js:316`, `author_mcp.py:104`.

**Límite encontrado:** Hay objetivos, rúbricas y tipos de ejercicio; no aparece ficha estructurada de formato real del parcial en estas rutas.

**Cambio:** Registrar formato declarado, duración, recursos permitidos y tipos de desempeño esperados con fuente.

**Aceptación:** El plan distingue examen oral, desarrollo o múltiple opción sin inferir probabilidades de examen.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G35 · Contexto controlado por el estudiante

Estado: **existe**. Prioridad: **P1**.

**Base de Glosa:** `web/context.js:15`, `web/context.js:79`, `tutor_context.py:139`.

**Límite encontrado:** Hay selección de documentos, páginas, notas e historial y preview; es un flujo separado del problema puntual.

**Cambio:** Presets por parcial o tarea que muestren selección efectiva y advertencias de presupuesto antes de preguntar, conservando el bloqueo explícito sin truncamiento silencioso.

**Aceptación:** Una pregunta puede reutilizar el alcance del parcial y ver exactamente qué fuentes e historial se enviarán.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G36 · Búsqueda contextual explicable

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `tutor_context.py:114`, `web/context.js:95`.

**Límite encontrado:** La recuperación usa términos y scoring léxico por página; no equivale a cobertura semántica completa.

**Cambio:** Mostrar fragmentos recuperados, permitir fijar/descartar y ampliar consulta con sinónimos editables.

**Aceptación:** El usuario detecta una página relevante omitida y puede incorporarla sin afirmar exhaustividad de búsqueda.

**Referencia externa:** KO5; consultar alcance en EVIDENCIA.md.

### G37 · Abrir la fuente de una explicación

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/app.js:144`, `web/context.js:95`.

**Límite encontrado:** Las referencias de bloques abren URLs con página; manifiesto de contexto muestra documentos/páginas como texto. Además, safeSourceUrl rechaza /documents/ID aunque es el esquema del contrato: una prueba aislada de la función real devuelve null para /documents/doc-1.

**Cambio:** Corregir resolución de fuentes registradas y abrir citas en el lector integrado con regreso al chat/lección.

**Aceptación:** Una afirmación citada abre la página exacta y regresar mantiene pregunta y posición de conversación. /documents/ID, /sources/ y HTTPS válidos funcionan; se rechazan esquemas ajenos.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G38 · Separar consulta de evaluación

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/app.js:355`, `tutor_mcp.py:386`.

**Límite encontrado:** Consultar al tutor guarda respuesta y activa ayuda; contrato distingue feedback y assessment.

**Cambio:** Acciones claras explicar duda, guardar intento y evaluar evidencia, manteniendo registro de ayudas.

**Aceptación:** Pedir explicación no se presenta como acreditar; responder antes de ayuda queda identificable.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G39 · Búsqueda unificada de estudio

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `web/app.js:618`, `web/notes.js:317`, `web/study-tools.js:144`.

**Límite encontrado:** Lecciones, notas, títulos PDF y menciones tienen búsquedas separadas.

**Cambio:** Una búsqueda por concepto con resultados etiquetados en bloques, notas, PDFs, errores y ejercicios del alcance.

**Aceptación:** Cada resultado incluye contexto y destino exacto; se puede filtrar por parcial sin mezclar datos privados de otro pliego.

**Referencia externa:** KO5, OB-busqueda; consultar alcance en EVIDENCIA.md.

### G40 · Índice de encabezados de nota

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `web/notes.js:94`, `web/notes.js:124`.

**Límite encontrado:** Existen celdas por página y Markdown; el índice general de UI se refiere a lecciones.

**Cambio:** Índice plegable de encabezados de la nota y páginas con marcas y dudas.

**Aceptación:** Una nota larga permite saltar al encabezado y volver sin perder edición.

**Referencia externa:** OB-outline; consultar alcance en EVIDENCIA.md.

### G41 · Atajos descubribles y perfil estándar

Estado: **existe**. Prioridad: **P1**.

**Base de Glosa:** `web/keyboard.js:5`, `web/keyboard.js:154`, `web/keyboard.js:162`.

**Límite encontrado:** Hay perfiles, paleta y ayuda extensa; los comandos son un inventario general.

**Cambio:** Paleta contextual por vista y ayudas breves junto a acciones relevantes, con controles visibles equivalentes.

**Aceptación:** Un usuario con perfil estándar completa lectura/anotación/retorno sin memorizar Vim.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G42 · Audio de lectura como apoyo

Estado: **ausente**. Prioridad: **P2**.

**Base de Glosa:** `docs/pendientes.md:7`, `web/notes.js:476`.

**Límite encontrado:** Voz y seguimiento están explícitamente pendientes; no son capacidades actuales.

**Cambio:** Lectura opcional desde selección, velocidad y pausa con proveedor/costo explícito y sincronización limitada.

**Aceptación:** Detener audio conserva posición y escuchar no cambia estado de dominio.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G43 · Recuperación de conflictos comprensible

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `library.py:531`, `library.py:559`, `library.py:979`.

**Límite encontrado:** Se detectan revisiones y se preserva archivo de conflicto; no hay comparación visual en estas rutas.

**Cambio:** Interfaz para comparar local/servidor/archivo y elegir o fusionar sin perder ninguna versión.

**Aceptación:** Ediciones concurrentes se recuperan con ambas versiones visibles y IDs conservados.

**Referencia externa:** OB-metadatos; consultar alcance en EVIDENCIA.md.

### G44 · Versionar sin ocultar evidencia anterior

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `author_mcp.py:296`, `server.py:339`.

**Límite encontrado:** Se conserva historial y previousCourse; recomendación filtra eventos por versión actual.

**Cambio:** Relacionar criterios estables entre versiones y mostrar evidencia histórica pendiente de revalidar, sin acreditarla automáticamente. Diferenciar cambio editorial de cambio conceptual, mantener visible evidencia previa con su versión y exigir revisión antes de transferirla a un criterio nuevo.

**Aceptación:** Una edición tipográfica no hace invisible el historial; un cambio conceptual exige comprobación explicada.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G45 · Previsualización y revisión semántica editorial

Estado: **parcial**. Prioridad: **P0**.

**Base de Glosa:** `author_mcp.py:181`, `author_mcp.py:224`, `author_mcp.py:296`.

**Límite encontrado:** Hay chequeos, borradores y actualización atómica; la semántica no la garantiza validar formato.

**Cambio:** Informe revisable de cambios, fuentes, enlaces rotos y criterios afectados antes de activar versión.

**Aceptación:** El autor puede inspeccionar diff y revisión semántica separada; IDs e historial siguen trazables.

**Referencia externa:** OB-metadatos; consultar alcance en EVIDENCIA.md.

### G46 · Uso sin conexión y continuidad móvil

Estado: **parcial**. Prioridad: **P2**.

**Base de Glosa:** `web/notes.js:193`, `web/notes.js:195`, `web/app.js:66`.

**Límite encontrado:** Hay borrador local pero API y PDF se sirven desde servidor; no se observó service worker en la superficie revisada.

**Cambio:** Definir modo desconectado explícito para lecturas seleccionadas y cola local de operaciones con resolución de conflictos.

**Aceptación:** Sin conexión se informa qué está disponible; reconectar no duplica intentos ni pisa revisiones.

**Referencia externa:** Propuesta propia derivada del flujo de Glosa; no se presenta como extracción con REA.

### G47 · Autocompletar enlaces y destinos

Estado: **ausente**. Prioridad: **P1**.

**Base de Glosa:** `web/study-tools.js:105`.

**Límite encontrado:** Se resuelven títulos escritos; no hay selector integrado de destino con nota, encabezado y desambiguación.

**Cambio:** Elegir concepto/destino mientras se escribe, con ID estable y texto natural en la lección.

**Aceptación:** Escribir una referencia muestra destinos distinguibles y un cambio de título conserva su identidad.

**Referencia externa:** OB-enlaces; consultar alcance en EVIDENCIA.md.

### G48 · Incrustar una definición o sección sin duplicarla

Estado: **ausente**. Prioridad: **P2**.

**Base de Glosa:** `web/markdown.js:16`.

**Límite encontrado:** Los enlaces y previews no son transclusiones persistentes del contenido en una hoja de estudio.

**Cambio:** Referencia en solo lectura a una sección de una nota, indicando origen y versión; ciclos y límites explícitos.

**Aceptación:** Editar la fuente actualiza el bloque referenciado; un ciclo no cuelga el lector y siempre se puede abrir el origen.

**Referencia externa:** OB-embeds; consultar alcance en EVIDENCIA.md.

### G49 · Bloques de ejemplo, advertencia y ayuda plegable

Estado: **ausente**. Prioridad: **P1**.

**Base de Glosa:** `web/markdown.js:31`.

**Límite encontrado:** Hay blockquotes genéricos; la ficha mezcla definición, ejemplo y contraejemplo como encabezados.

**Cambio:** Bloques con etiqueta semántica y plegado opcional para ayuda/solución, sin adelantar respuestas durante un intento.

**Aceptación:** Se distinguen tipos sin depender solo del color, se manejan por teclado y la ayuda queda oculta hasta pedirla.

**Referencia externa:** OB-callouts; consultar alcance en EVIDENCIA.md.

### G50 · Fórmulas matemáticas legibles

Estado: **ausente**. Prioridad: **P1**.

**Base de Glosa:** `web/markdown.js:16`.

**Límite encontrado:** La lista de tokens renderizados no contiene matemática.

**Cambio:** Notación matemática local en lecciones, notas y previews; conservar código editable, accesibilidad y exportación.

**Aceptación:** Fracciones, matrices y expresiones inline/bloque se leen sin red; un signo monetario no se interpreta erróneamente.

**Referencia externa:** OTRA-matematica; consultar alcance en EVIDENCIA.md.

### G51 · Notas al pie y citas bidireccionales

Estado: **ausente**. Prioridad: **P1**.

**Base de Glosa:** `web/markdown.js:16`.

**Límite encontrado:** No hay token/flujo de notas al pie en el render revisado.

**Cambio:** Cita breve en el párrafo, fuente en nota al pie y retorno al marcador; no sustituir documento/página por texto sin trazabilidad.

**Aceptación:** Abrir una cita y volver conserva posición; referencias sin definición y fuentes inaccesibles se informan.

**Referencia externa:** OTRA-pies; consultar alcance en EVIDENCIA.md.

### G52 · Etiquetas y vistas de repaso guardadas

Estado: **parcial**. Prioridad: **P2**.

**Base de Glosa:** `web/study-tools.js:587`.

**Límite encontrado:** Hay filtros por materia/unidad/fecha/práctica, pero no vistas guardadas por dificultad o patrón transversal.

**Cambio:** Guardar búsquedas/filtros como «errores de unidades» o «argumentación pendiente», con alcance visible por parcial.

**Aceptación:** La vista se reconstruye desde datos existentes, no crea otra copia de errores y nunca transforma etiquetas en dominio.

**Referencia externa:** OTRA-etiquetas; consultar alcance en EVIDENCIA.md.

### G53 · Diagramas para explicar procesos y relaciones

Estado: **ausente**. Prioridad: **P2**.

**Base de Glosa:** `web/markdown.js:27`.

**Límite encontrado:** Los bloques de código se presentan como texto; no hay render de diagramas.

**Cambio:** Diagramas locales editables de procesos/arquitecturas, acompañados de una consigna para explicar relaciones y límites.

**Aceptación:** El esquema puede contrastarse con la fuente y el estudiante debe explicar una relación; ver o generar un dibujo no acredita comprensión.

**Referencia externa:** OTRA-diagramas; consultar alcance en EVIDENCIA.md.

### G54 · Hoja de repaso por parcial exportable

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `library.py:32`.

**Límite encontrado:** Se exportan apuntes/historial/bóveda, no una selección integrada por examen.

**Cambio:** Exportar errores, dudas, fichas, preguntas pendientes y fuentes elegidos por materia/parcial; decidir si incluir respuestas aparte.

**Aceptación:** Lo exportado coincide con la selección guardada y sus fuentes; no inventa resúmenes ni envía datos automáticamente.

**Referencia externa:** KO3; consultar alcance en EVIDENCIA.md.

### G55 · Anotar regiones, tablas y esquemas

Estado: **parcial**. Prioridad: **P1**.

**Base de Glosa:** `web/notes.js:432`.

**Límite encontrado:** Los rectángulos actuales se calculan desde rangos de texto; no hay selección directa de una región sin texto.

**Cambio:** Seleccionar una figura o celda de tabla con referencia a página/rectángulo, explicación propia y enlace al original.

**Aceptación:** Se marca un esquema escaneado sin OCR, conserva su región al hacer zoom y puede usarse como fuente de una pregunta.

**Referencia externa:** OTRA-regiones; consultar alcance en EVIDENCIA.md.

### G56 · Comparar fuentes en vistas fijadas

Estado: **parcial**. Prioridad: **P2**.

**Base de Glosa:** `web/notes.js:406`.

**Límite encontrado:** La división actual es fuente+apunte; no es una comparación fija de dos páginas/documentos o dos explicaciones.

**Cambio:** Fijar dos referencias sin perder la lección; permitir anotar qué coincide, qué difiere y qué queda incierto.

**Aceptación:** Cambiar de página en una vista no mueve la otra; el retorno recupera la tarea y cada cita identifica su propia fuente.

**Referencia externa:** PROPIA-comparacion; consultar alcance en EVIDENCIA.md.

### G57 · Importar anotaciones de otros lectores con procedencia

Estado: **ausente**. Prioridad: **P2**.

**Base de Glosa:** `library.py:254`.

**Límite encontrado:** El esquema de Glosa admite anclas, pero no se observó importador de sidecars de KOReader/Okular en el flujo revisado.

**Cambio:** Importación explícita con vista previa, hash del documento, mapeo de página/posición y separación entre cita, comentario e inferencia.

**Aceptación:** Un desajuste de documento o posición se informa; no se ejecuta un sidecar Lua como programa ni se duplica una anotación ya importada.

**Referencia externa:** OTRA-sidecars; consultar alcance en EVIDENCIA.md.

### G58 · Rotación y recorte visual por documento

Estado: **parcial**. Prioridad: **P2**.

**Base de Glosa:** `web/notes.js:476`.

**Límite encontrado:** El visor tiene zoom; getViewport recibe scale y no hay controles de rotación/recorte en el flujo revisado.

**Cambio:** Rotación y márgenes visuales reversibles para tablas o filminas, conservando coordenadas del PDF original.

**Aceptación:** Rotar/recortar no cambia el archivo ni desplaza las anclas; deshacer vuelve a la vista original.

**Referencia externa:** OTRA-geometria; consultar alcance en EVIDENCIA.md.
