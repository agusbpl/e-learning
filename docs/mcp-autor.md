# Autoría de cursos con un agente externo

El tutor integrado conversa durante el estudio mediante el proveedor configurado. OpenRouter conserva su selección de modelos gratuitos. La autoría usa el modelo del programa externo que elijas. Este MCP no necesita una clave del tutor y no hace solicitudes a un proveedor de modelos. El costo o la cuota del agente externo dependen de tu programa y cuenta.

Sirve tanto para crear una materia desde cero como para preparar una continuación. Tus notas de clase existen de forma independiente del curso y del PDF. En **Notas**, marcá **Compartir este apunte con el agente que crea cursos** únicamente en los apuntes que quieras incluir. Las versiones anteriores y las notas privadas quedan fuera del contexto automático del autor.

## Elegir pliego

`list_rooms` enumera las pliegos registradas; `open_room(room_id)` selecciona la pliego
para TODAS las consultas y modificaciones posteriores de esa conexión MCP.
La selección es independiente del navegador. `author_brief` devuelve `roomId`.
`import_room(folder, title)` importa un paquete completo en otra pliego;
`export_room(folder)` exporta la seleccionada a una carpeta nueva con PDFs y hashes.
No sobrescribe historiales ni hace push a Git. Abrí explícitamente la pliego correcta
antes de preparar una continuación o cambiar su calendario.

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
| `save_course_draft(course, rationale)` | Guarda una propuesta para revisar en Notas → Cursos preparados. No importa ni reemplaza un curso. |
| `pending_continuations(course_id)` | Encargos explícitos Preparar continuación sin aplicar. |
| `continuation_brief(request_id)` | Curso y encargo, regla, apuntes compartidos y primera página de historial. Completar paginación con study_history. |
| `apply_continuation(request_id, course, expected_version, rationale)` | Activa directamente un curso completo para ese encargo; exige versión nueva, conserva versión anterior e historial y rechaza conflictos. |
| `list_calendar_events(course_id)` | Calendario del curso, sin inventar horarios. |
| `save_calendar_event(event, expected_revision)` | Crear/editar clase, práctica, entrega, examen o estudio; date, hora opcional y repeatUntil para repetición semanal. |
| `delete_calendar_event(event_id, expected_revision)` | Quitar un evento cuando el usuario lo encargue, comprobando la revisión. |

El agente puede leer los PDFs locales registrados con sus propias herramientas; el MCP no enumera archivos ajenos a la biblioteca. Las notas compartidas son material del estudiante: debe distinguir opiniones y dudas de lo que afirman las fuentes y seguir el encargo humano. Las respuestas y conversaciones pueden contener información personal que escribiste directamente en ellas.

## Encargo de ejemplo para una materia nueva

> Usá estudio-autor para preparar un curso nuevo de {{materia}}. Consultá author_brief con folder={{carpeta}} y sin course_id. Mi objetivo es {{objetivo}}, el alcance es {{temario}} y dispongo de {{tiempo}} hasta {{fecha}}. Inventariá las fuentes y mis apuntes compartidos. Personalizá el prompt de autor para esta materia; redactá teoría rigurosa y referenciada, actividades que exijan explicar y relacionar, y ayudas progresivas. Justificá los recursos y simulaciones por su utilidad pedagógica. Indicá faltantes y qué dudas motivan cada explicación. Validá el curso completo y guardalo con save_course_draft, explicando los criterios. No lo actives automáticamente.

Para una continuación, agregá `course_id`, consultá todas las páginas pertinentes de `study_history`, conservá IDs cuando el significado no cambie e incrementá la versión del curso. No tratar una respuesta con ayuda como evidencia independiente ni asumir que una duda quedó resuelta porque se escribió una explicación.

Revisá **Notas → Cursos preparados**; allí podés leer el JSON, descargarlo o incorporarlo. La lista consulta los borradores recientes al abrirse. La aplicación y el MCP deben usar el mismo directorio de datos. El valor predeterminado es `.local-data`; `LEARNING_DATA_DIR` permite cambiarlo para pruebas o bibliotecas distintas.

## Comprobación

```bash
.venv-author/bin/python scripts/check_author_mcp.py
```

Usa una base temporal que se elimina al terminar. Comprueba lectura, privacidad, historial, validación y entrega del borrador sin alterar tus apuntes ni llamar a un modelo.


El encargo de `author_brief` incluye `evaluationRules`, la regla fuerte contra pistas de preguntas y sesgos de evaluación. `validate_course` devuelve además `itemQuality`; `save_course_draft` exige corregir sus señales mecánicas. `randomize_positions(count)` ofrece permutaciones mediante la fuente criptográfica del sistema, para no pedir azar al LLM. En Codex está instalado el skill `estudio-evaluar`; otros agentes reciben la misma regla por el MCP, sin depender de que su programa soporte skills de Codex.

`author_brief` entrega en `promptTemplate` y `courseContract` las responsabilidades del autor para videos: consultar contenido, comprobar disponibilidad y permiso de incrustación, justificar su relación con el objetivo, elegir el inicio y preparar una consigna concreta y contexto textual para el tutor. Entrega recursos JSON y declara lo que no pudo comprobar. `validate_course` controla forma, ID, título, consigna y segundos de inicio; devuelve avisos sobre las comprobaciones externas pendientes, sin acreditarlas. El código de la plataforma resuelve el reproductor directo, la carga diferida, la política de referencia, la ausencia de autoplay y el lanzador local. Ambos documentos se leen en cada consulta.

## Margen y Primer trazo

`list_rooms` conserva su nombre por compatibilidad y ahora descubre los pliegos del Margen además de los anteriores; devuelve la carpeta configurada, respaldos y avisos. `open_room` selecciona el pliego por su ID estable. `create_pliego(title)` crea uno vacío; `configure_margen(folder)` define el directorio existente sin mover datos. `GLOSA_MARGEN_DIR` prevalece sobre el ajuste guardado.

`primer-trazo` es un tutorial separado. Elegí el pliego real del encargo antes de leer historial o guardar cursos; las prácticas del tutorial no describen la materia del estudiante. La interfaz lo abre cuando el navegador no tiene una selección; el MCP mantiene el pliego local como selección inicial por compatibilidad.
