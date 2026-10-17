# Auditoría funcional de Glosa orientada a parciales

Lectura estática de código y documentación el 17/10/2026. No ejecuté pruebas, no abrí bases, materiales ni credenciales. No son bugs reproducidos. `existe` significa que hay implementación visible; `parcial` que existe la base o un flujo aislado; `ausente` que no encontré el flujo en las rutas inspeccionadas. Prioridades P0: estudiar/comprobar con trazabilidad; P1: integración y facilidad; P2: ampliación posterior.

Se revisaron AGENTS.md y docs/evaluacion-rigurosa.md. Las mejoras propuestas conservan independencia, incertidumbre, azar del sistema cuando corresponde y distinción entre tiempo, autoevaluación y dominio. No se implementó nada.

## G01 · Buscar texto dentro del PDF (ausente; P0)

Área: PDF. Evidencia estática: `web/notes.js:267`, `web/notes.js:476`, `tutor_context.py:114`.

Límite observado en fuente: El selector busca títulos; paint carga texto de una página. Hay recuperación textual para el tutor, no una interfaz de coincidencias del lector.

Cambio: Buscar frase y términos con resultados por página, contexto y navegación anterior/siguiente.

Aceptación propuesta: Una consulta encuentra coincidencias de varias páginas y cada resultado abre y señala el fragmento.

## G02 · Índice jerárquico del documento (ausente; P1)

Área: PDF. Evidencia estática: `web/notes.js:458`, `web/notes.js:476`.

Límite observado en fuente: La ruta de carga/render inspeccionada no solicita getOutline.

Cambio: Mostrar índice nativo del PDF; usar índice manual claramente identificado cuando no exista.

Aceptación propuesta: Elegir una sección abre su destino; un documento sin índice no muestra un índice inventado.

## G03 · Navegación de páginas visible (parcial; P1)

Área: PDF. Evidencia estática: `web/notes.js:456`, `web/notes.js:493`.

Límite observado en fuente: El contador existe, pero pdf-page es un input hidden y el avance depende de comandos.

Cambio: Añadir salto visible por número, anterior/siguiente y etiquetas de página si el PDF las tiene.

Aceptación propuesta: Se puede saltar a página válida sin conocer atajos; se distingue página PDF de numeración impresa.

## G04 · Continuidad entre páginas (parcial; P2)

Área: PDF. Evidencia estática: `web/notes.js:275`, `web/notes.js:476`.

Límite observado en fuente: El lector dibuja una sola página; readStep cambia al llegar al borde.

Cambio: Ofrecer desplazamiento continuo con renderizado acotado y conservar modo página.

Aceptación propuesta: El scroll atraviesa tres páginas sin vacíos ni crecimiento de canvases ilimitado.

## G05 · Volver al lugar exacto (parcial; P0)

Área: PDF. Evidencia estática: `web/notes.js:458`, `web/notes.js:476`, `web/notes.js:253`.

Límite observado en fuente: Se conserva página y paint permite preservar proporción al zoom; el salto de nota no implementa una pila general de retornos.

Cambio: Historial de ubicaciones con página, desplazamiento, bloque y selección/borrador.

Aceptación propuesta: Abrir nota desde una lección y volver restaura párrafo y borrador; navegar por fuente restaura desplazamiento PDF.

## G06 · Enlaces internos y externos del PDF (ausente; P1)

Área: PDF. Evidencia estática: `web/notes.js:476`.

Límite observado en fuente: paint crea canvas y TextLayer, sin AnnotationLayer ni resolución de destinos en la ruta inspeccionada.

Cambio: Renderizar enlaces del PDF, destinos internos y política segura para externos.

Aceptación propuesta: Un enlace de índice y una referencia interna abren el destino correcto; un enlace externo se identifica.

## G07 · Selección a pregunta o ficha (parcial; P0)

Área: PDF. Evidencia estática: `web/notes.js:449`, `web/notes.js:500`, `web/study-tools.js:173`.

Límite observado en fuente: Se puede resaltar, comentar y consultar; la ficha se inserta aparte como plantilla.

Cambio: Crear una ficha/pregunta desde la selección con cita, hash, página y enlace de regreso.

Aceptación propuesta: La pregunta conserva la cita y localización y no registra dominio por crear la ficha.

## G08 · Lectura de escaneos (parcial; P1)

Área: PDF. Evidencia estática: `library.py:194`, `web/notes.js:476`.

Límite observado en fuente: Hay extracción y TextLayer; en estas rutas no hay flujo de OCR ni advertencia específica por página sin texto.

Cambio: Detectar páginas sin texto y ofrecer OCR local opcional conservando original y procedencia.

Aceptación propuesta: Un escaneo informa que no tiene texto; el texto OCR se etiqueta y se puede corregir sin reemplazar el PDF.

## G09 · Marcadores de lectura (ausente; P2)

Área: PDF. Evidencia estática: `web/notes.js:409`, `web/notes.js:493`.

Límite observado en fuente: Hay anclas de anotación y página actual; no hay lista dedicada de marcadores sin comentario.

Cambio: Guardar marcadores nombrados por documento y recuperarlos desde la lección.

Aceptación propuesta: Se marca una página sin escribir comentario y se recupera tras recargar.

## G10 · Accesibilidad del contenido PDF (parcial; P1)

Área: PDF. Evidencia estática: `web/notes.js:476`.

Límite observado en fuente: Canvas tiene aria-label y existe TextLayer; esta ruta no crea árbol estructural del documento.

Cambio: Vista de texto accesible por página con encabezados cuando existan y navegación de lectura.

Aceptación propuesta: Un lector de pantalla recorre el contenido sin depender de coordenadas ni del canvas.

## G11 · Conceptos enlazados en la lección (existe; P0)

Área: Notas y conceptos. Evidencia estática: `web/app.js:185`, `web/app.js:230`, `author_mcp.py:279`.

Límite observado en fuente: Existe enlace nativo estable y render compatible con resaltados; la autoría debe insertar los enlaces.

Cambio: Añadir revisión editorial de términos relevantes sin links y selector de nota durante autoría; mantener texto natural.

Aceptación propuesta: Los términos se consultan dentro del párrafo; nunca se agrega un glosario previo obligatorio.

## G12 · Preview contextual del concepto (existe; P1)

Área: Notas y conceptos. Evidencia estática: `web/app.js:191`.

Límite observado en fuente: La preview renderiza note.content completo; omite pageNotes y no contextualiza la acepción por lección.

Cambio: Conservar preview y permitir resumen/acepción pertinente, fuente y expandir contenido largo.

Aceptación propuesta: Un concepto largo muestra una definición útil sin desbordar; sigue funcionando foco y Escape.

## G13 · Consulta de conceptos en táctil (parcial; P1)

Área: Notas y conceptos. Evidencia estática: `web/app.js:211`, `web/app.js:213`.

Límite observado en fuente: pointerover ignora touch y el clic navega directamente a la nota.

Cambio: Ofrecer acción táctil para preview y otra para abrir sin perder ubicación.

Aceptación propuesta: Un usuario táctil puede leer definición y cerrar manteniendo la lección en el mismo lugar.

## G14 · Unificar enlaces por ID y wikilinks (parcial; P0)

Área: Notas y conceptos. Evidencia estática: `web/app.js:185`, `web/study-tools.js:105`, `web/study-tools.js:132`.

Límite observado en fuente: Los enlaces nativos son por ID; referencias inversas de StudyTools siguen títulos exactos de wikilinks.

Cambio: Resolver ambas sintaxis a identidad de nota y mostrar backlinks también desde bloques de curso.

Aceptación propuesta: Renombrar una nota no rompe referencias resueltas y un link nativo de lección aparece en sus backlinks.

## G15 · Ambigüedad y alias de conceptos (parcial; P1)

Área: Notas y conceptos. Evidencia estática: `web/study-tools.js:105`, `web/study-tools.js:138`.

Límite observado en fuente: La resolución documentada usa título exacto normalizado; no hay selección por materia o acepción.

Cambio: Alias y selector de destino cuando coinciden títulos; no enlazar automáticamente homónimos.

Aceptación propuesta: SI puede resolver a una nota elegida y dos conceptos iguales de materias distintas no se confunden.

## G16 · Ficha como práctica recuperable (parcial; P0)

Área: Notas y conceptos. Evidencia estática: `web/study-tools.js:173`, `web/study-tools.js:373`.

Límite observado en fuente: La ficha es texto añadido al final de una nota, no una actividad con intento independiente.

Cambio: Permitir responder pregunta de ficha ocultando definición y registrar intento ligado a criterio explícito.

Aceptación propuesta: Se puede responder antes de ver el contenido y la evaluación no confunde rellenar plantilla con evidencia.

## G17 · Registro de errores y reintento (parcial; P0)

Área: Notas y conceptos. Evidencia estática: `web/study-tools.js:271`, `web/study-tools.js:542`.

Límite observado en fuente: Registro personal y corrección existen separados de los intentos y evaluaciones.

Cambio: Enlazar error con ejercicio, criterio y fuente; generar caso nuevo para comprobar resolución.

Aceptación propuesta: Un error sigue pendiente hasta una comprobación nueva; su corrección previa no se muestra antes del intento.

## G18 · Conceptos con relaciones explicadas (parcial; P2)

Área: Notas y conceptos. Evidencia estática: `web/study-tools.js:132`, `web/study-tools.js:144`.

Límite observado en fuente: Backlinks y menciones indican conexión textual, sin relación conceptual tipada.

Cambio: Relaciones pequeñas como se diferencia de, requiere, aplica a con explicación y fuente dentro de notas.

Aceptación propuesta: Una comparación abre ambos conceptos y conserva su justificación; no depende de un grafo global.

## G19 · Cola de repaso por criterio (parcial; P0)

Área: Práctica y evaluación. Evidencia estática: `server.py:334`, `tutor_mcp.py:386`.

Límite observado en fuente: La recomendación principal agrega por lección; sí hay criterionChecks en evaluación.

Cambio: Construir cola de criterios pendientes y frágiles, ordenada por parcial y evidencia independiente.

Aceptación propuesta: Dos criterios con estados distintos generan tareas distintas sin trasladar dominio entre ellos.

## G20 · Retención después de acreditar (parcial; P0)

Área: Práctica y evaluación. Evidencia estática: `server.py:350`, `tutor_modes.py:372`.

Límite observado en fuente: recommend omite lecciones independent; el caso todas acreditadas solo recomienda repaso integrador.

Cambio: Agendar comprobaciones espaciadas de recuperación con plazos explícitos y posibilidad de ajustar.

Aceptación propuesta: Una lección acreditada reaparece para comprobación sin borrar su evidencia previa ni inventar olvido medido.

## G21 · Simulacro con corrección diferida (ausente; P0)

Área: Práctica y evaluación. Evidencia estática: `web/app.js:316`, `web/app.js:355`.

Límite observado en fuente: saveAnswer revela feedback choice antes de terminar el flujo de consulta; no hay objeto sesión de examen en esta ruta.

Cambio: Sesión de simulacro que fije preguntas y orden y revele correcciones al terminar.

Aceptación propuesta: No se ve clave durante el intento y al terminar se conserva respuesta original, orden, ayudas y feedback.

## G22 · Tiempo de simulacro (parcial; P1)

Área: Práctica y evaluación. Evidencia estática: `web/app.js:546`, `web/app.js:620`.

Límite observado en fuente: Existe tiempo estimado de estudio/sesión visible; no es un cronómetro por intento de simulacro.

Cambio: Cronómetro opcional con pausa e interrupciones diferenciadas; distinguir inconcluso de error conceptual.

Aceptación propuesta: El vencimiento no convierte automáticamente una respuesta incompleta en falta de comprensión.

## G23 · Intercalación de unidades (parcial; P0)

Área: Práctica y evaluación. Evidencia estática: `web/app.js:162`, `server.py:334`.

Límite observado en fuente: Actividades se presentan según secuencia de una lección y recomendación elige una lección.

Cambio: Sesiones mixtas por alcance confirmado y criterios, con selección trazable y azar del sistema cuando corresponda.

Aceptación propuesta: Una sesión combina unidades incluidas sin sumar temario externo ni repetir la misma clave revelada.

## G24 · Reformular casos después de ayuda (parcial; P0)

Área: Práctica y evaluación. Evidencia estática: `tutor_mcp.py:386`, `docs/evaluacion-rigurosa.md:28`.

Límite observado en fuente: La regla exige aplicación nueva; el formulario conserva el mismo ejercicio y prior response.

Cambio: Acción explícita Pedir comprobación nueva ligada al criterio, con versión y fuente verificadas.

Aceptación propuesta: Después de ayuda se evalúa un caso distinto y se identifica la respuesta como independiente o asistida.

## G25 · Tablero de evidencia por criterio (parcial; P0)

Área: Práctica y evaluación. Evidencia estática: `web/app.js:432`, `tutor_mcp.py:386`.

Límite observado en fuente: Hay detalles de contexto y evidencia y estado de lección; falta una vista transversal estructurada por criterio.

Cambio: Mostrar criterio, cita del estudiante, estado, independencia, fecha y próxima comprobación.

Aceptación propuesta: Cada estado visible se puede rastrear a ejercicio, respuesta y cita real sin mostrar una nota numérica ficticia.

## G26 · Historial comparativo de intentos (parcial; P1)

Área: Práctica y evaluación. Evidencia estática: `web/app.js:319`, `web/app.js:468`.

Límite observado en fuente: Se guardan respuestas en eventos y se muestra la última en formulario/cuaderno; no hay comparación dirigida por criterio.

Cambio: Comparar intentos de un mismo criterio y separar qué cambió tras explicación o transferencia.

Aceptación propuesta: El usuario ve ambas respuestas originales y las ayudas intermedias sin sobrescribir historial.

## G27 · Incertidumbre y reclamo de evaluación (parcial; P1)

Área: Práctica y evaluación. Evidencia estática: `tutor_mcp.py:386`, `docs/evaluacion-rigurosa.md:27`.

Límite observado en fuente: El contrato admite estados de criterio inciertos y reglas; el flujo de apelación no está en la UI inspeccionada.

Cambio: Acción revisar criterio que adjunte respuesta, rúbrica y fuente y deje auditoría de reevaluación.

Aceptación propuesta: Una reevaluación conserva el dictamen previo y explica cambio o incertidumbre con fuentes.

## G28 · Práctica de producción no textual (parcial; P2)

Área: Práctica y evaluación. Evidencia estática: `web/app.js:316`, `server.py:133`.

Límite observado en fuente: La UI de ejercicio admite choice y textarea de explicación/aplicación.

Cambio: Adjuntar desarrollo, esquema o imagen para materias que lo requieran; criterios que evalúen su contenido.

Aceptación propuesta: Un procedimiento manuscrito se conserva como evidencia y el tutor explicita límites de lectura de la imagen.

## G29 · Alcance confirmado del parcial (existe; P0)

Área: Planificación. Evidencia estática: `author_mcp.py:386`, `tutor_mcp.py:620`, `tutor_modes.py:357`.

Límite observado en fuente: Existe propuesta/confirmación de temario; el calendario local crea eventos sin seleccionar alcance en el formulario.

Cambio: Integrar selección y confirmación de unidades/notas al evento de parcial desde UI.

Aceptación propuesta: Un parcial tiene alcance visible con procedencia y estado confirmado o propuesto antes de planificar.

## G30 · Plan global y siguiente acción ejecutable (parcial; P0)

Área: Planificación. Evidencia estática: `web/tutor-modes.js:87`, `tutor_modes.py:488`.

Límite observado en fuente: El plan global lista cobertura y postergación; planRow muestra títulos como texto.

Cambio: Cada tarea debe abrir lección, fuente o comprobación concreta y volver al plan.

Aceptación propuesta: Desde una prioridad global se abre la tarea exacta del pliego correcto con un clic.

## G31 · Dos planificadores coherentes (parcial; P0)

Área: Planificación. Evidencia estática: `server.py:334`, `tutor_modes.py:488`, `web/plan.js:35`.

Límite observado en fuente: Conviven recomendación local y asignación global con modelos diferentes de selección.

Cambio: Alinear motivo de siguiente tarea entre Hoy, recomendación de curso y Parciales, mostrando conflictos explícitos.

Aceptación propuesta: La tarea recomendada indica si corresponde al curso o al plan global y explica cualquier diferencia.

## G32 · Presupuesto y replanificación por hechos (parcial; P1)

Área: Planificación. Evidencia estática: `server.py:317`, `tutor_modes.py:445`.

Límite observado en fuente: Existen disponibilidades, asignación y tiempos; duración no acredita dominio.

Cambio: Replanificar por tareas realizadas/evidencia y disponibilidad corregida, con vista previa de qué queda afuera.

Aceptación propuesta: Una sesión corta no marca dominio y el cambio de disponibilidad muestra tareas postergadas antes de aplicarse.

## G33 · Eventos globales editables (parcial; P1)

Área: Planificación. Evidencia estática: `web/plan.js:8`, `web/plan.js:56`, `author_mcp.py:369`.

Límite observado en fuente: El calendario por fecha filtra curso; hay vista global de parciales.

Cambio: Calendario conjunto con filtro por materia/pliego y detección de compromisos superpuestos.

Aceptación propuesta: Dos parciales de distintos pliegos aparecen juntos sin duplicar eventos ni inventar horarios.

## G34 · Preparación según formato docente (parcial; P1)

Área: Planificación. Evidencia estática: `web/app.js:316`, `author_mcp.py:104`.

Límite observado en fuente: Hay objetivos, rúbricas y tipos de ejercicio; no aparece ficha estructurada de formato real del parcial en estas rutas.

Cambio: Registrar formato declarado, duración, recursos permitidos y tipos de desempeño esperados con fuente.

Aceptación propuesta: El plan distingue examen oral, desarrollo o múltiple opción sin inferir probabilidades de examen.

## G35 · Contexto controlado por el estudiante (existe; P1)

Área: Tutor y contexto. Evidencia estática: `web/context.js:15`, `web/context.js:79`, `tutor_context.py:139`.

Límite observado en fuente: Hay selección de documentos, páginas, notas e historial y preview; es un flujo separado del problema puntual.

Cambio: Presets por parcial o tarea que muestren selección efectiva antes de preguntar y advertencias al truncar.

Aceptación propuesta: Una pregunta puede reutilizar el alcance del parcial y ver exactamente qué fuentes e historial se enviarán.

## G36 · Búsqueda contextual explicable (parcial; P1)

Área: Tutor y contexto. Evidencia estática: `tutor_context.py:114`, `web/context.js:95`.

Límite observado en fuente: La recuperación usa términos y scoring léxico por página; no equivale a cobertura semántica completa.

Cambio: Mostrar fragmentos recuperados, permitir fijar/descartar y ampliar consulta con sinónimos editables.

Aceptación propuesta: El usuario detecta una página relevante omitida y puede incorporarla sin afirmar exhaustividad de búsqueda.

## G37 · Abrir la fuente de una explicación (parcial; P0)

Área: Tutor y contexto. Evidencia estática: `web/app.js:144`, `web/context.js:95`.

Límite observado en fuente: Las referencias de bloques abren URLs con página; manifiesto de contexto muestra documentos/páginas como texto.

Cambio: Citas del tutor y del manifiesto clicables hacia lector integrado con regreso al chat.

Aceptación propuesta: Una afirmación citada abre la página exacta y regresar mantiene pregunta y posición de conversación.

## G38 · Separar consulta de evaluación (parcial; P0)

Área: Tutor y contexto. Evidencia estática: `web/app.js:355`, `tutor_mcp.py:386`.

Límite observado en fuente: Consultar al tutor guarda respuesta y activa ayuda; contrato distingue feedback y assessment.

Cambio: Acciones claras explicar duda, guardar intento y evaluar evidencia, manteniendo registro de ayudas.

Aceptación propuesta: Pedir explicación no se presenta como acreditar; responder antes de ayuda queda identificable.

## G39 · Búsqueda unificada de estudio (parcial; P0)

Área: Navegación y accesibilidad. Evidencia estática: `web/app.js:618`, `web/notes.js:317`, `web/study-tools.js:144`.

Límite observado en fuente: Lecciones, notas, títulos PDF y menciones tienen búsquedas separadas.

Cambio: Una búsqueda por concepto con resultados etiquetados en bloques, notas, PDFs, errores y ejercicios del alcance.

Aceptación propuesta: Cada resultado incluye contexto y destino exacto; se puede filtrar por parcial sin mezclar datos privados de otro pliego.

## G40 · Índice de encabezados de nota (parcial; P1)

Área: Navegación y accesibilidad. Evidencia estática: `web/notes.js:94`, `web/notes.js:124`.

Límite observado en fuente: Existen celdas por página y Markdown; el índice general de UI se refiere a lecciones.

Cambio: Índice plegable de encabezados de la nota y páginas con marcas y dudas.

Aceptación propuesta: Una nota larga permite saltar al encabezado y volver sin perder edición.

## G41 · Atajos descubribles y perfil estándar (existe; P1)

Área: Navegación y accesibilidad. Evidencia estática: `web/keyboard.js:5`, `web/keyboard.js:154`, `web/keyboard.js:162`.

Límite observado en fuente: Hay perfiles, paleta y ayuda extensa; los comandos son un inventario general.

Cambio: Paleta contextual por vista y ayudas breves junto a acciones relevantes, con controles visibles equivalentes.

Aceptación propuesta: Un usuario con perfil estándar completa lectura/anotación/retorno sin memorizar Vim.

## G42 · Audio de lectura como apoyo (ausente; P2)

Área: Navegación y accesibilidad. Evidencia estática: `docs/pendientes.md:7`, `web/notes.js:476`.

Límite observado en fuente: Voz y seguimiento están explícitamente pendientes; no son capacidades actuales.

Cambio: Lectura opcional desde selección, velocidad y pausa con proveedor/costo explícito y sincronización limitada.

Aceptación propuesta: Detener audio conserva posición y escuchar no cambia estado de dominio.

## G43 · Recuperación de conflictos comprensible (parcial; P1)

Área: Persistencia y autoría. Evidencia estática: `library.py:531`, `library.py:559`, `library.py:979`.

Límite observado en fuente: Se detectan revisiones y se preserva archivo de conflicto; no hay comparación visual en estas rutas.

Cambio: Interfaz para comparar local/servidor/archivo y elegir o fusionar sin perder ninguna versión.

Aceptación propuesta: Ediciones concurrentes se recuperan con ambas versiones visibles y IDs conservados.

## G44 · Versionar sin ocultar evidencia anterior (parcial; P0)

Área: Persistencia y autoría. Evidencia estática: `author_mcp.py:296`, `server.py:339`.

Límite observado en fuente: Se conserva historial y previousCourse; recomendación filtra eventos por versión actual.

Cambio: Relacionar criterios estables entre versiones y mostrar evidencia histórica pendiente de revalidar, sin acreditarla automáticamente.

Aceptación propuesta: Una edición tipográfica no hace invisible el historial; un cambio conceptual exige comprobación explicada.

## G45 · Previsualización y revisión semántica editorial (parcial; P0)

Área: Persistencia y autoría. Evidencia estática: `author_mcp.py:181`, `author_mcp.py:224`, `author_mcp.py:296`.

Límite observado en fuente: Hay chequeos, borradores y actualización atómica; la semántica no la garantiza validar formato.

Cambio: Informe revisable de cambios, fuentes, enlaces rotos y criterios afectados antes de activar versión.

Aceptación propuesta: El autor puede inspeccionar diff y revisión semántica separada; IDs e historial siguen trazables.

## G46 · Uso sin conexión y continuidad móvil (parcial; P2)

Área: Persistencia y autoría. Evidencia estática: `web/notes.js:193`, `web/notes.js:195`, `web/app.js:66`.

Límite observado en fuente: Hay borrador local pero API y PDF se sirven desde servidor; no se observó service worker en la superficie revisada.

Cambio: Definir modo desconectado explícito para lecturas seleccionadas y cola local de operaciones con resolución de conflictos.

Aceptación propuesta: Sin conexión se informa qué está disponible; reconectar no duplica intentos ni pisa revisiones.

## Integraciones prioritarias

- Enlace de lección por ID ↔ backlinks por título: unificar identidad sin reconstruir un glosario aparte.
- Error personal ↔ respuesta ↔ criterio evaluado ↔ caso nuevo: hoy son capacidades separadas.
- Plan global ↔ recomendación local ↔ tarea ejecutable: reconciliar motivos y navegación.
- Selección PDF ↔ ficha ↔ práctica ↔ fuente: conservar cita y comprobar recuperación independiente.
- Contexto usado ↔ citas del tutor ↔ lector ↔ retorno exacto: completar circuito de verificación.
- Historial de versión ↔ evidencia histórica: conservar visibilidad sin acreditar por transferencia automática.
