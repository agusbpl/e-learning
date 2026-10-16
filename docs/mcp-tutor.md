# Conversación con el tutor desde un agente externo

El tutor integrado conversa durante el estudio con el proveedor configurado en Ajustes. Este MCP permite el mismo flujo desde un cliente o agente externo cuando no tenés clave, tokens o cuota: **la respuesta la produce el modelo de tu programa externo** (tu cuenta y su costo); Glosa no llama a ningún proveedor por esta vía y no comparte su clave. Es un servidor separado del MCP de autoría (`author_mcp.py`): no guarda cursos ni modifica el historial de autoría; comparte el pliego, la selección de contexto y los eventos para que la conversación quede trazada en tu registro.

## Conexión

El servidor usa stdio y el mismo runtime local `.venv-author`. El comando es:

```text
/ruta/absoluta/glosa/start-tutor-mcp.sh
```

Un cliente que acepte configuración JSON con `mcpServers` puede usar:

```json
{
  "mcpServers": {
    "estudio-tutor": {
      "command": "/ruta/absoluta/glosa/start-tutor-mcp.sh"
    }
  }
}
```

Los MCP de autoría y de tutor pueden estar conectados en simultáneo: son procesos separados con pliegos independientes por conexión. La plataforma debe correr contra el mismo directorio de datos (`LEARNING_DATA_DIR`, con `.local-data` por omisión). El servidor de tutor no necesita `OPENROUTER_API_KEY` ni ninguna credencial del tutor; si no hay clave, funciona igual.

## Elegir pliego

`list_pliegos()` enumera los pliegos del Margen y anteriores; `open_pliego(room_id)` selecciona el pliego para toda esa conexión MCP, sin depender del navegador. La selección inicial es el pliego local por compatibilidad. Elegí el pliego correcto antes de leer historial o registrar conversaciones: `primer-trazo` es el tutorial y no describe tu materia.

## Herramientas

| Herramienta | Uso |
|---|---|
| `list_pliegos()` | Pliegos disponibles y avisos del Margen. |
| `open_pliego(room_id)` | Selecciona el pliego por su ID estable para esta conexión. |
| `tutor_courses()` | Cursos con lecciones, prerrequisitos y estado de evidencia de la versión vigente; plan vigente de horas. |
| `tutor_brief(course_id, lesson_id)` | Contexto completo para conversar: material según la selección del tutor, ejercicios y respuestas, conversación reciente del tema, reglas de evaluación, contrato y hash de contexto. |
| `tutor_conversation(course_id, lesson_id, offset, limit)` | Conversación paginada del curso con IDs para citar; sin respuesta cruda ni trazas de contexto. |
| `register_tutor_exchange(...)` | Registra el intercambio: pregunta del estudiante, tu respuesta externa, evaluación opcional y propuesta de cuaderno, con IDs, traza de contexto y puerta de evidencia. |
| `tutor_pending()` | Consultas pendientes del canal MCP: preguntas de lección sin respuesta (creadas por la interfaz o un intento interrumpido) y apuntes con registro `note_tutor` pendiente. También funciona en bóvedas sin cursos. |
| `tutor_note_brief(request_id, note_id)` | Material de un apunte elegido por la selección del tutor (igual que el tutor de Notas integrado): nota o páginas del PDF, historial de esa pieza, traza y hash. Con `request_id` responde un pendiente; con `note_id` lee otro apunte. |
| `register_note_exchange(...)` | Responde un pendiente de apunte con tu modelo externo y trazabilidad; la explicación es ayuda recibida y nunca acredita dominio. |

No hay herramienta de envío a un proveedor ni de simulación de respuestas: si no pasás `reply` y `model_name`, no se registra nada.

## Flujo de conversación

1. Elegí pliego y pedí `tutor_brief` de la lección vigente. El brief incluye el payload de contexto exacto que usaría el tutor integrado (lección, fuentes citadas, anotaciones compartidas, historial), sus advertencias, `contextHash` y las reglas de [evaluación rigurosa](evaluacion-rigurosa.md).
2. Leé la conversación previa con `tutor_conversation` si necesitás más de las últimas 12 intervenciones del tema.
3. Con tu propio modelo, respondé con tu evaluación opcional: `status`, `evidence`, `gaps`, `nextAction`, `criterionChecks` con citas literales del estudiante. Ante incertidumbre, usá `pending` o `uncertain` y registrá solo la conversación.
4. Registrá el intercambio con `register_tutor_exchange`, un `request_id` opaco nuevo por consulta y tu `model_name`. Repetir el mismo `request_id` con el mismo contenido no duplica eventos; con otro contenido se rechaza. Si el curso podría haber cambiado de versión, pasá `expected_course_version`.
5. El estudiante sigue respondiendo las actividades en la interfaz local; la corrección de opciones es determinista de la plataforma y la plataforma actualizará la ayuda recibida en la próxima respuesta.

Si la selección de contexto cambió en la interfaz entre tu brief y tu registro, el evento lo deja en evidencia: `contextHashVerified: false` y el hash solicitado conservado en la traza.

## Flujo de apuntes y PDF (con o sin cursos)

El canal MCP externo también cubre consultas de apuntes privados o compartidos (tutor de Notas), en bóvedas con o sin cursos:

1. La interfaz guarda la consulta como registro `note_tutor` pendiente con canal `mcp` (no llama a proveedores). `tutor_pending()` la lista con su `requestId`, `noteId`, mensaje y un resumen del contexto (el texto completo y las páginas del PDF se piden con `tutor_note_brief`).
2. Con `tutor_note_brief(request_id=...)` recibís el material congelado de la consulta: nota, página del PDF con su texto extraído, historial reciente de esa pieza, `manifest`, selección, `contextHash` y un contrato específico. Si el apunte cambió desde la consulta, `noteRevisionChanged: true` te avisa; con `expected_note_revision` en el registro podés exigir la revisión que viste.
3. Respondé la duda con tu proveedor y registrá con `register_note_exchange(request_id, note_id, question, reply, model_name, ...)`: `context_hash` (el del brief) se verifica contra los materiales vigentes; la evaluación es opcional y limitada (`pending`/`with_help`, `evidence`, `gaps`, `reason`, `followUp`). `independent`, `criterionChecks` y `notebook` se rechazan: consultar apuntes es ayuda recibida, no comprensión demostrada.
4. La respuesta queda en el registro `note_tutor` del pliego: la interfaz de apuntes la muestra al recargar, sin cambiar el estado de ninguna lección ni crear eventos de curso.

El material que entrega `tutor_note_brief` respeta la misma forma que el mensaje del tutor de Notas integrado: el payload completo está en `context` y la parte del apunte (título, revisión, página, texto del estudiante, cita) está anidada en `context.context`; el `contextHash` que pasás en `register_note_exchange` se calcula sobre ese mismo payload (con la parte del apunte bajo la clave `context`), igual que hace la API.

## Registro atómico e idempotencia

- **Lecciones:** `register_tutor_exchange` escribe pregunta, respuesta, evaluación y notas del cuaderno en una única transacción SQLite (`BEGIN IMMEDIATE`): si algo falla a mitad de camino no queda nada en disco y el `request_id` queda libre para reintentar. La identidad del intercambio (`exchangeSha256`) cubre texto, curso/lección/versión, actividad (`exerciseId`), modelo y evaluación: reusar un `request_id` ya registrado con cualquier argumento distinto se rechaza, y repetir exactamente la misma llamada devuelve el registro existente sin duplicar ni modificar nada. Si la interfaz ya creó la pregunta pendiente con `id = <request_id>-pregunta`, la fila y su contexto se conservan intactos y solo se completa la respuesta.
- **Apuntes:** `register_note_exchange` actualiza el registro `note_tutor` en una única transacción; compara el `request_id` contra apunte, mensaje, modelo y evaluación, y repite exacta (`alreadyRegistered: true`) sin tocar la marca temporal ni la pregunta. Los pendientes del canal integrado (`api`) no pueden ser respondidos por el agente externo.

## Registro y trazabilidad

- **IDs:** la pregunta se guarda como evento `chat_message` con ID `<request_id>-pregunta` y la respuesta como `tutor_reply` con ID `request_id`; la evaluación, si corresponde, como evento `assessment`; el cuaderno propuesto, como eventos `tutor_note` vinculados con `sourceEventId`. Un registro interrumpido puede reintentarse con el mismo ID y se completa sin duplicar (ver "Registro atómico e idempotencia").
- **Contexto:** la respuesta registra `tutorContext` igual que el tutor integrado: selección, revisiones, materiales, hash del payload efectivo (`contextHash`, calculado con la pregunta real) y `briefContextSha256`, con `provider: external-mcp` y el nombre del modelo externo. Si pasás `context_hash` (el del brief), el evento indica si coincidió. Para apuntes, la traza viven en el registro `note_tutor` con `provider`, `model` y la revisión del apunte al responder.
- **Evaluación:** la misma puerta de evidencia del tutor integrado aplica al assessment externo. Los criterios de opción múltiple se acreditan con la justificación (campo `reasoning` de la respuesta), no con la opción elegida. `independent` exige citas literales del estudiante para *todos* los criterios y respuesta registrada para toda actividad de la lección en esta versión; si falta algo, degrada a `pending` con el motivo guardado.
- **Ayuda recibida:** el intercambio registrado es un `tutor_reply` del historial: la próxima respuesta que el estudiante guarde en la interfaz queda marcada `helpReceived`; conversar con el agente externo es ayuda recibida, no evidencia independiente. En apuntes rige lo mismo por diseño: la consulta marca `helpProvided` y la explicación no acredita comprensión.

## Interfaz y sincronización

La interfaz lee el historial al iniciar y tras cada acción (`reload()`); no mantiene un canal en vivo. Un intercambio registrado por el MCP aparece en el panel de conversación al recargar la página (F5) o con cualquier acción posterior que recargue la lección. El panel identifica la procedencia con `data.source = external-mcp` y `data.model`: la etiqueta visible es una mejora pendiente documentada para la interfaz, pero no bloquea el uso: el registro ya está en el historial, los respaldos, el cuaderno y el historial de autoría con las mismas reglas.

## Privacidad

- Solo el curso, los apuntes y el historial del pliego elegido; anotaciones y apuntes entran al contexto por las mismas decisiones de la interfaz (`Contexto` y `shareWithTutor`). Las privadas quedan fuera a menos que alguien las elija explícitamente. En los pendientes listados por `tutor_pending` no se vuelcan todavía las páginas completas del PDF: eso ocurre solo al pedir `tutor_note_brief`.
- No se navega ni se descarga contenido de enlaces; el material llega solo por lo que el estudiante eligió. Exportar el historial incluye estas conversaciones registradas.

## Comprobación

```bash
.venv-author/bin/python -m unittest tests.test_tutor_mcp -v   # Pruebas del MCP con base temporal
.venv-author/bin/python scripts/check_tutor_mcp.py             # Integración stdio real con base temporal
```

Ambas usan bases temporales que se eliminan al terminar; nunca llaman a un modelo ni alteran tu historial real.
