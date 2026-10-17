# Autoría de cursos con un agente externo

El tutor integrado conversa durante el estudio mediante el proveedor configurado. OpenRouter conserva su selección de modelos gratuitos. La autoría usa el modelo del programa externo que elijas. Este MCP no necesita una clave del tutor y no hace solicitudes a un proveedor de modelos. El costo o la cuota del agente externo dependen de tu programa y cuenta.

Sirve tanto para crear una materia desde cero como para preparar una continuación. Tus notas de clase existen de forma independiente del curso y del PDF. En **Notas**, marcá **Compartir este apunte con el agente que crea cursos** únicamente en los apuntes que quieras incluir. Las versiones anteriores y las notas privadas quedan fuera del contexto automático del autor.

## Flujo predeterminado: carpeta → pliego completo

El estudiante puede pedir: **«Usá el MCP de autoría para crear un pliego con /ruta/a/materiales»**.
Ese encargo autoriza crear el material completo y dejarlo listo para estudiar.

Glosa puede redactar el encargo: **GLOSA → Preparar una materia con mi agente**.
El selector navega carpetas de la computadora donde corre Glosa y devuelve solo
nombres y rutas; no carga archivos. El estudiante elige si el agente debe proponer
la ruta o si quiere indicar examen, fecha, hora, temario y disponibilidad.
La vista previa es editable y **Copiar** la lleva al portapapeles para pegarla en
su agente. No ejecuta un modelo, conecta programas ni crea datos de estudio.
El encargo indica el directorio de fuentes, el Margen de destino y los datos
opcionales escritos por el estudiante, sin añadir preferencias pedagógicas.
Incluye el comando stdio de esta instalación e instruye al agente a configurar
y conectar el MCP si no está disponible, y continuar con el encargo.

1. Consultá `source_folder_brief(folder)` y leé las fuentes autorizadas de esa carpeta.
   No consultes otras materias ni historiales. El inventario devuelve rutas relativas,
   hashes e IDs deterministas para PDFs. Markdown, texto UTF-8 y PDF son compatibles;
   otros formatos requieren conversión previa y se informan como omitidos.
2. Redactá el curso completo: teoría didáctica con siglas explicadas, objetivos,
   referencias localizables, ruta de estudio, actividades, simulacros y refuerzos
   según el encargo. Revisá semántica y cobertura además de la validación mecánica.
3. Llamá `create_study_pliego(folder, title, course, rationale, calendar_events,
   study_plan, source_files)`. Los últimos tres argumentos son opcionales;
   `source_files` permite limitarse a archivos relativos concretos. No inventes
   fechas, horas ni disponibilidad: registrá solo lo indicado o acordado.
4. El resultado es **un directorio dentro del Margen configurado** (`~/Margen`
   por defecto), con `pliego.json`, `learning/`, `assets/`, `Apuntes/` y trazabilidad
   en `autoria.json`. Fuentes, curso activo, plan y calendario quedan incorporados.
   El estudiante pulsa **GLOSA → Margen → nombre del pliego** y empieza.

**Sin ZIP, importación ni paso por Notas.** La publicación es atómica: si falla una
fuente, el curso o el calendario, no aparece un pliego incompleto. Nunca sobrescribe
otro directorio ni reinicia historiales. El agente es quien redacta y revisa el
contenido; el MCP no llama a un modelo ni convierte un inventario en una lección.
Los Markdown largos se dividen en apuntes conservando íntegro su contenido.
Los PDFs se copian con extracción por página, sin OCR. Las referencias PDF usan
`/documents/ID` con el `documentId` del inventario.

## Pliegos existentes y continuaciones

`list_rooms` enumera los pliegos; `open_room(room_id)` selecciona uno para esa conexión.
`author_brief` entrega contrato, plantilla y contexto autorizado del pliego seleccionado.
Para una continuación explícita usá `pending_continuations`, `continuation_brief`,
paginá `study_history` y entregá con `apply_continuation`, conservando IDs e historial.
`create_pliego(title)` queda para un pedido explícito de pliego vacío.
`save_course_draft` se mantiene por compatibilidad con clientes anteriores, pero no
forma parte del flujo nuevo ni tiene una bandeja de importación en Notas.

## Conexión

El servidor usa stdio. Instalá el runtime local `.venv-author` con las dependencias de `requirements-author.txt`. El comando es:

```text
/ruta/absoluta/glosa/start-author.sh
```

El cliente debe ejecutar ese archivo como servidor MCP. Un cliente que acepte configuración JSON con `mcpServers` puede usar:

```json
{
  "mcpServers": {
    "estudio-autor": {
      "command": "/ruta/absoluta/glosa/start-author.sh"
    }
  }
}
```

El formato de configuración depende del cliente. No se modificaron configuraciones de Codex, Antigravity ni otros programas. La prueba de integración verifica stdio con el SDK oficial y los protocolos actual y de inicialización anterior; la conexión dentro de esos programas todavía debe comprobarse.

Para instalar las dependencias en otra computadora, usá Python 3.11 o superior con el módulo venv disponible, desde la raíz del proyecto:

```bash
python3 -m venv .venv-author
.venv-author/bin/python -m pip install -r requirements-author.txt
```

## Herramientas

| Herramienta | Uso |
|---|---|
| `author_brief(folder, course_id)` | Prompt personalizable, contrato, ejemplo, apuntes actuales compartidos y curso opcional. Sin `course_id` sirve para una materia nueva. |
| `list_documents()` | PDFs registrados, huellas, páginas, URL para el curso y archivo local. |
| `read_document_pages(document_id, start, end)` | Texto extraído de hasta 20 páginas por consulta. No incluye OCR. |
| `study_history(course_id, offset, limit)` | Respuestas originales, dudas compartidas, ayudas, feedback y tiempo del curso, con paginación. |
| `validate_course(course)` | Estructura del JSON y referencias a PDFs registrados. No comprueba calidad pedagógica. |
| `source_folder_brief(folder, source_files)` | Inventario de la carpeta autorizada, IDs PDF, contrato y reglas. |
| `create_study_pliego(...)` | Crea el directorio completo en el Margen, listo para abrir desde GLOSA. |
| `pending_continuations(course_id)` | Encargos explícitos Preparar continuación sin aplicar. |
| `continuation_brief(request_id)` | Curso y encargo, regla, apuntes compartidos y primera página de historial. Completar paginación con study_history. |
| `apply_continuation(request_id, course, expected_version, rationale)` | Activa directamente un curso completo para ese encargo; exige versión nueva, conserva versión anterior e historial y rechaza conflictos. |
| `list_calendar_events(course_id)` | Calendario del curso, sin inventar horarios. |
| `save_calendar_event(event, expected_revision)` | Crear/editar clase, práctica, entrega, examen o estudio; date, hora opcional y repeatUntil para repetición semanal. |
| `delete_calendar_event(event_id, expected_revision)` | Quitar un evento cuando el usuario lo encargue, comprobando la revisión. |

El agente puede leer los PDFs locales registrados con sus propias herramientas; el MCP no enumera archivos ajenos a la biblioteca. Las notas compartidas son material del estudiante: debe distinguir opiniones y dudas de lo que afirman las fuentes y seguir el encargo humano. Las respuestas y conversaciones pueden contener información personal que escribiste directamente en ellas.

## Encargo de ejemplo

> Usá el MCP de autoría para crear un pliego con /ruta/a/materiales. Rindo el
> martes a las 19; entra hasta la última clase de teoría. Puedo estudiar sábado,
> lunes y martes; domingo solo un simulacro breve. Explicá todas las siglas y
> prepará simulacros diarios, con uno holístico el martes. Dejalo completo en
> el Margen configurado, listo para abrir desde GLOSA.

La aplicación y el MCP deben compartir el directorio de datos (`LEARNING_DATA_DIR`,
`.local-data` por defecto) y la configuración de Margen. `GLOSA_MARGEN_DIR` prevalece
sobre el ajuste guardado y sobre `~/Margen`. No cambiarlos para autoría habitual.

## Comprobación

```bash
.venv-author/bin/python scripts/check_author_mcp.py
```

Usa una base temporal que se elimina al terminar. Comprueba lectura, privacidad, historial, validación y compatibilidad del borrador legado y entrega directa de pliegos sin alterar tus apuntes ni llamar a un modelo.


El encargo de `author_brief` incluye `evaluationRules`, la regla fuerte contra pistas de preguntas y sesgos de evaluación. `validate_course` devuelve además `itemQuality`; `save_course_draft` exige corregir sus señales mecánicas. `randomize_positions(count)` ofrece permutaciones mediante la fuente criptográfica del sistema, para no pedir azar al LLM. En Codex está instalado el skill `estudio-evaluar`; otros agentes reciben la misma regla por el MCP, sin depender de que su programa soporte skills de Codex.

`author_brief` entrega en `promptTemplate` y `courseContract` las responsabilidades del autor para videos: consultar contenido, comprobar disponibilidad y permiso de incrustación, justificar su relación con el objetivo, elegir el inicio y preparar una consigna concreta y contexto textual para el tutor. Entrega recursos JSON y declara lo que no pudo comprobar. `validate_course` controla forma, ID, título, consigna y segundos de inicio; devuelve avisos sobre las comprobaciones externas pendientes, sin acreditarlas. El código de la plataforma resuelve el reproductor directo, la carga diferida, la política de referencia, la ausencia de autoplay y el lanzador local. Ambos documentos se leen en cada consulta.

## Margen y Primer trazo

`list_rooms` conserva su nombre por compatibilidad y ahora descubre los pliegos del Margen además de los anteriores; devuelve la carpeta configurada, respaldos y avisos. `open_room` selecciona el pliego por su ID estable. `create_pliego(title)` crea uno vacío; `configure_margen(folder)` define el directorio existente sin mover datos. `GLOSA_MARGEN_DIR` prevalece sobre el ajuste guardado.

`primer-trazo` es un tutorial separado. Elegí el pliego real del encargo antes de leer historial o guardar cursos; las prácticas del tutorial no describen la materia del estudiante. La interfaz lo abre cuando el navegador no tiene una selección; el MCP mantiene el pliego local como selección inicial por compatibilidad.

### Notas nativas y edición puntual

`save_native_note(note)` crea una nota nativa en el pliego seleccionado y devuelve
`note` y `url` (`#note=ID`). Para editar, enviar el ID y la revisión actual.
Un glosario puede enlazarla con `[SI](#note=ID)`; el lector abre ese apunte en Notas.
`update_course_block(course_id, lesson_id, block_id, text, expected_version,
new_version, rationale)` modifica únicamente el texto de un bloque existente,
comprueba la versión y archiva el curso anterior, conservando IDs e historial.

`update_course_blocks(course_id, changes, expected_version, new_version, rationale)`
aplica varias ediciones en una transacción. Cada cambio identifica `lessonId` y
`blockId`, con `text` nuevo o `remove: true` para retirar explícitamente ese bloque.
Cualquier bloque inválido o conflicto de versión cancela el conjunto completo.
Los enlaces a conceptos se insertan en la prosa de las lecciones, donde aparecen
los términos; no requieren un bloque separado de glosario. Distinguir siglas como
`SI` de palabras comunes como `si` al revisar los enlaces.
