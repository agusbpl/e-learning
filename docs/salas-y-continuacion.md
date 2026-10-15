# Pliegos, Margen y ciclo de aprendizaje

Glosa organiza espacios de estudio independientes con sus propios datos.

## Lo que funciona ahora

El curso es el contenedor de las lecciones, con ID y versión. Notas y documentos pertenecen a una biblioteca global; la carpeta de una nota es una clasificación, no una relación formal con una cursada. La disponibilidad y la fecha de examen de Ajustes son globales. El calendario nuevo está asociado a cada curso y permite teoría, práctica, entrega, examen y estudio, con repetición semanal opcional. No crea clases ni franjas de estudio inventadas.

Importar acepta un curso completo JSON o el respaldo de la aplicación, hasta 8 MB. Un curso existente requiere versión nueva si cambió; se conserva el anterior. Restaurar incorpora eventos por ID, conserva relaciones y rechaza cursos, revisiones o eventos de calendario incompatibles con los locales. No reemplaza silenciosamente otra versión.

Exportar JSON guarda todos los cursos, ajustes, eventos originales, anotaciones, notas y revisiones, conversaciones, selección de contexto, borradores y calendario. Incluye notas privadas. Markdown es el diario legible del registro. El selector **GLOSA / Abrir salas** importa y abre entornos completos independientes, desde ZIP o carpeta clonada de Git. Exporta ZIP con JSON, PDFs, cachés y Markdown legible; valida hashes y usa una copia consistente de la base. Cada sala tiene su propio directorio, biblioteca, calendario y ajustes. El modelo interno de cada sala sigue permitiendo varios cursos, pero no implementa todavía entidades de parcial ni disponibilidad por examen. Git es respaldo manual, sin sincronización o fusión automática.

## Cuaderno y evidencia

Cuaderno muestra primero anotaciones explícitas del estudiante y apuntes breves del tutor. El tutor puede proponer hasta tres dudas, relaciones conceptuales o decisiones de repaso por consulta, o ninguna. Cada propuesta exige una cita literal del mensaje actual; las citas inventadas, entradas mal formadas y repeticiones exactas de la misma lección/versión no se publican como apuntes. Esto verifica atribución y estructura; el modelo sigue siendo responsable de la calidad semántica de su síntesis.

El registro original permanece completo para reconstruir el aprendizaje y revisar una mala síntesis. Una nota del tutor es una interpretación, nunca evidencia de dominio por sí sola. Las ayudas siguen registradas y una respuesta posterior a una explicación del grupo se marca como asistida. Los intercambios anteriores no se sintetizan retroactivamente ni se borran.

## Preparar continuación

El estudiante usa **Preparar continuación**. Se guarda `continuation_requested`, con curso, lección, versión e IDs de evidencia compartida. No cambia el dominio ni activa un modelo. Codex, Antigravity u otro cliente MCP debe estar ejecutándose y recibir el encargo de procesar la cola.

El agente consulta `pending_continuations` y `continuation_brief`; pagina **todo** `study_history`, revisa rúbricas y fuentes y redacta un curso completo actualizado. Puede insertar una mini lección de refuerzo, preparar una comprobación de transferencia o una evaluación integradora. `apply_continuation` lo activa directamente para ese encargo explícito: exige versión nueva y versión esperada, conserva el curso anterior y el historial, rechaza conflictos y evita aplicar dos veces el mismo encargo. No elimina lecciones existentes. Fuera de ese flujo sigue disponible guardar borradores para revisión.

Las versiones de curso siguen siendo la unidad actual de evaluación: cambiarla puede dejar pendientes comprobaciones de lecciones anteriores. Antes de automatizar continuaciones largas, el modelo de salas debe pasar a versionar evidencia por contenido y rúbrica de cada lección, conservando acreditación únicamente cuando ese contenido, fuentes y criterios no hayan cambiado. No trasladar dominio por coincidencia del ID.

El agente debe separar **prioridad pedagógica** de **solidez de evidencia**. Prioridad considera prerrequisitos, objetivos del parcial, recurrencia y tiempo. Evidencia distingue opción corregida mecánicamente, explicación independiente, explicación asistida, síntesis del tutor e incertidumbre. No inventar un porcentaje de dominio ni tratar la confianza del tutor como medición. Toda decisión debe citar eventos y criterios. Un concepto importante sin evidencia sólida merece una comprobación breve; más evaluaciones solo se justifican si añaden evidencia útil.

## Modelo óptimo de sala: próxima evolución

Una sala por **materia y cursada**, con parciales, recuperatorios y entregas como objetivos internos. Su ID estable agrupa programa, fuentes, curso/recorridos, notas, diario, calendario, disponibilidad, objetivos, historial y cola de continuación. Una nota puede compartir una fuente sin duplicar el PDF; se explicita a qué sala pertenece y qué puede leer el autor. Ajustes de interfaz/proveedor son globales; fechas, presupuesto de estudio, calendario y prioridades son de la sala.

Plan conserva ese nombre y abre **Hoy**: próximo compromiso, tiempo disponible y siguiente actividad. Semana permite ver clases y estudio; Mes sitúa entregas y parciales. La navegación de trabajo usa Estudiar/Notas/Cuaderno/Plan y un selector convocable, distinto de NORMAL/INSERT. El usuario eligió la hoja clara de la propuesta 1 con el calendario de 2.

La importación debe ofrecer tres operaciones claras: abrir una sala nueva, restaurar una copia de la misma sala o incorporar una continuación. Vista previa con nombres, versiones, fuentes faltantes y conflictos antes de escribir; importación atómica y comprobación de integridad. IDs iguales no autorizan sobrescribir datos distintos. La restauración conserva registros originales y revisiones, no fusiona textos de apuntes por conjetura.

Paquete propuesto `sala.zip`: `manifest.json` con versión/ID/revisión/huellas, `room.json` con materia y objetivos, `courses/`, `notes/` Markdown y metadatos de páginas, `events.jsonl`, `notebook.json`, `calendar.json`, `plan.json`, `assets/` con PDF autorizados y sus textos extraídos. No incluir claves ni estado de dispositivos Tailscale. Verificar rutas, tamaños, huellas y relaciones antes de importar. Exportar sobre una lectura consistente de la base; restaurar el paquete en una base temporal para comprobar que el respaldo abre.

El MCP debe disponer de inventario y creación de salas, lectura de programa/evidencia, fuentes y apuntes autorizados, agenda, objetivos, plan, cola, aplicación de continuaciones, exportación y restauración. Usar control de revisiones y herramientas explícitas por operación. El MCP conecta al agente con esos datos; no es un motor autónomo que se despierta sin un cliente.

## GitHub como respaldo

Mantener el repositorio del programa público y un repositorio **privado separado** para salas personales. El usuario eligió incluir también PDF autorizados. Versionar JSON/Markdown y documentos por huella, con un commit por respaldo coherente; evitar subir de nuevo un ZIP binario completo en cada sesión. Mantener además una copia local recuperable y probar restauraciones. Una publicación educativa compartible debe poder excluir historial personal y material sin permiso de redistribución.

No usar Git como sincronización de SQLite en vivo. Antes de enviar: preparar una exportación consistente, comprobar integridad y restaurabilidad, validar que el destino sea el repositorio privado configurado y que no contenga credenciales. Los archivos grandes pueden requerir otra política: [GitHub bloquea archivos mayores de 100 MiB y advierte desde 50 MiB](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). [La visibilidad del repositorio define quién puede acceder](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility). Git LFS tiene sus propios límites y cuotas; no dar por supuesto que un respaldo con muchos PDFs será gratuito indefinidamente.

El selector, la importación/exportación completa y el respaldo privado ya están implementados. El paquete actual usa manifest.json, snapshot.json, PDFs y cachés bajo root/data, más vistas Markdown; la estructura de room.json, parciales y planificación por examen de arriba sigue siendo una propuesta.

## Actualización: Margen y Primer trazo

La interfaz llama pliegos a las salas. Margen descubre subcarpetas con `pliego.json`, `learning/learning.sqlite3` y `assets/`; abrirlas conserva identidad y guarda directamente, sin importar una copia. Los registros y APIs `rooms` existentes mantienen sus identificadores. Las carpetas de respaldos se ofrecen como importación de una copia, nunca como una sincronización.

Primer trazo es el inicio para navegadores sin un pliego seleccionado. Tiene un curso de uso, actividades y una demo local; sus datos se guardan por separado en `tutorial/`. No se incorpora a los cursos reales ni modifica su historial. El directorio por defecto es `margen/` dentro del directorio de datos; el selector permite otro directorio existente y `GLOSA_MARGEN_DIR` lo puede fijar al arrancar.
