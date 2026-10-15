# Elegir lo que recibe el tutor

Abrí **Contexto** junto al chat o `g x`. En Notas, el mismo comando abre la selección del apunte actual; los diálogos de preguntas y anotaciones tienen un acceso propio. Abrir el gestor no consulta a ningún modelo. Se maneja con Tab, Shift+Tab, Space, flechas y Enter; Esc cierra sin aplicar cambios. Guardar aplica la selección para consultas futuras, compartida entre PC y celular. Durante una consulta en curso se conserva la selección capturada al iniciarla.

El gestor permite incluir o excluir la lección completa, el apunte/comentario actual, sus páginas citadas, historial reciente y fecha/disponibilidad. La consulta escrita y las reglas del tutor se envían siempre. Sin la lección ni su rúbrica, la conversación de estudio no genera una evaluación de dominio. El tutor de Notas nunca acredita comprensión.

## Fuentes

- **Texto completo** envía todas las páginas con texto extraído del PDF seleccionado, sin un recorte silencioso por número de páginas. Se probó con el libro local de 643 páginas y un proveedor simulado; eso no garantiza que cualquier modelo gratuito admita su extensión.
- **Páginas elegidas** acepta números y rangos como `1-5, 8, 12`. El servidor valida los límites del PDF antes de guardar la selección.
- **Buscar en todo el documento** usa búsqueda local de palabras ponderadas por frecuencia para elegir hasta seis páginas coincidentes con la consulta. Es recuperación léxica, sin embeddings ni llamadas adicionales al LLM. No equivale a enviar el libro completo. La vista previa muestra las páginas y el modelo recibe ese alcance explícito. Si no hay coincidencias, no se rellenan con páginas arbitrarias.
- **Adjuntar fuente PDF** registra un documento mediante la misma extracción y límite de 20 MB de Notas y lo selecciona en el borrador del gestor. Guardá para aplicarlo. El PDF no se manda como archivo al modelo: se envía su texto extraído. No se hace OCR.
- **Pegar fuente de texto** permite agregar título, contenido y enlace HTTPS opcional. El enlace es una referencia; no se navega ni se descarga su contenido automáticamente.

Las páginas repetidas se envían una sola vez, con documento, título, número PDF y huella SHA-256. Se advierten páginas sin texto, fuentes ausentes y extracciones incompletas. La selección automática inicial sigue las páginas citadas por la lección o el comentario de lectura.

## Anotaciones y privacidad

Cada anotación de estudio tiene un checkbox propio, incluyendo las personales. La selección inicial incluye las compartidas de la materia actual y excluye las personales. Al personalizarla, una anotación privada entra solo por selección explícita. Esto no modifica `shareWithTutor` ni la opción de compartir apuntes con el autor externo.

En **Apuntes y anotaciones de lectura** se puede elegir texto general, páginas específicas y comentarios individuales. Elegir una parte no agrega las restantes. Las anotaciones antiguas sin ID se identifican por su contenido original; si cambian, quedan fuera con advertencia en vez de seleccionar otro comentario por su posición.

El historial es una elección aparte: hasta 70 eventos significativos del curso y sus últimas evaluaciones, o hasta seis consultas respondidas del mismo comentario/página en Notas. Excluye los registros de anotaciones, que se agregan por sus checkboxes, y elimina respuestas crudas y trazas de contexto de los eventos enviados. Sin embargo, mensajes y respuestas anteriores pueden contener citas de material ahora desmarcado: para excluir también esas citas hay que desmarcar **Historial reciente**. No hay una eliminación semántica automática de fragmentos de conversaciones anteriores.

Las exportaciones personales incluyen las elecciones, fuentes de texto y respuestas. Compartir un apunte y sus consultas con el autor externo puede revelar citas de las fuentes que usaste en esa conversación. Revisá esa elección al compartir; elegir contexto del tutor no convierte por sí mismo un apunte privado en compartido.

## Vista previa y límites

**Previsualizar contexto** muestra el material, páginas, historial y texto ensamblado usando la consulta indicada. Una búsqueda cambia con el mensaje real; la vista previa no reserva páginas para una consulta distinta. La vista previa no consume cuota del modelo.

La plataforma mide caracteres, no tokens. Bloquea llamadas con más de tres millones de caracteres de contenido, sin truncarlos ni cambiar silenciosamente de selección. Un modelo gratuito puede tener un límite menor y rechazar un contexto permitido por la plataforma; usá páginas o búsqueda en ese caso. El presupuesto de proveedor sigue limitado a precio cero para entrada y salida, sin servicios pagos ni llamadas de resumen automáticas.

Cada respuesta nueva incluye **Contexto utilizado**, con revisión, materiales, páginas, advertencias y cantidad de historial. El registro exportable conserva selección, revisiones de apuntes/anotaciones, huellas de documentos y hash del payload efectivo. No se duplica todo el libro en cada evento. Las notas conservan además su contexto original para seguir la duda. Esto registra qué se envió, no garantiza exactitud ni comprensión del modelo.

La selección vive en `library.tutorContexts`, con control de revisión para evitar sobrescribir cambios entre dispositivos. Los respaldos anteriores sin ese campo siguen siendo compatibles. Restaurar no sobrescribe una selección local posterior; si una misma revisión difiere, se rechaza el conflicto. El MCP de autoría no recibe automáticamente las preferencias privadas de contexto.

## Comprobaciones

`tests/test_learning.py` prueba exclusión de material, inclusión explícita de notas privadas, páginas, recuperación léxica, libro completo con proveedor simulado, ausencia de evaluación sin lección, persistencia, restauración, conflictos y límites. `tests/browser_context.cjs` recorre selección, desmarcado, fuentes de texto, adjuntos, notas y celular con servidor/base temporales y proveedor simulado. Los recorridos de estudio, Notas y MCP también usan bases temporales. No se hacen llamadas reales a modelos para estas pruebas.
