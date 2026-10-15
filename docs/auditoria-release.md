# Auditoría de la primera release

Fecha inicial: 14 de octubre de 2026. Este documento conserva el registro
cronológico de la revisión. El estado vigente está en [release.md](release.md);
las decisiones y resultados posteriores sustituyen los pendientes anteriores.

## Decisión de publicación

La consulta a GitHub confirmó que `agusbpl/glosa` **ya es público** y que los
10 commits alcanzables del checkout también están publicados. Contienen nombres
y correos personales de autor y committer; varios blobs históricos conservan
rutas del equipo. Una corrección en el último commit o una regla de `.gitignore`
no elimina esos datos. Cambiar la visibilidad requiere una decisión explícita
del responsable y no retira copias ya descargadas.

El responsable decidió mantenerlo público y resolver el historial después.
Se registra esa decisión; no se cambió la visibilidad ni se reescribió la historia.

Usar el árbol filtrado que prepara `scripts/prepare_release.py` como contenido
de la release y revisar el commit y tag exactos, incluidos los archivos
«Source code» generados por GitHub. Para una historia pública nueva, elegir
una identidad pública de commit. Conservar
una copia privada del repositorio de trabajo y los datos privados por separado.
El tratamiento de la exposición del historial que ya está en GitHub queda pendiente
por esa decisión. El procedimiento
y los pasos pendientes están en [release.md](release.md).

## Privacidad y distribución

- La distribución se construye mediante una lista explícita de archivos,
  `release-files.json`; no contiene `.git`, bases, credenciales, PDFs, fuentes
  académicas, cachés de lectura, exportaciones, capturas ni grabaciones privadas.
- Se excluyen los dos cursos de materia del árbol de trabajo, sus generadores
  específicos y la documentación de planificación personal. El ejemplo público
  y el ejemplo del MCP usan `courses/tutorial.json`.
- Se quitaron rutas personales, referencias al repositorio privado de respaldos
  y datos del plan de examen en código y documentación distribuible. Las
  instalaciones nuevas empiezan sin minutos de estudio asignados; el cambio
  no reescribe los ajustes ya guardados.
- Las pruebas generan cursos, PDFs, respuestas y claves ficticias en directorios
  temporales. No necesitan material de estudio personal. El respaldo de un
  pliego sigue siendo privado y puede incluir notas e historial originales.
- La comparación literal de la credencial local disponible no encontró
  coincidencias en el candidato examinado ni en los 344 blobs históricos
  alcanzables. Los valores no se imprimieron ni se enviaron a agentes externos.
- La revisión inicial por patrones no encontró claves privadas ni tokens de
  formatos habituales en los 172 blobs de texto históricos elegibles. Ese
  escaneo excluyó binarios, dependencias y archivos grandes. No hubo OCR.

El filtrado y los patrones no garantizan detectar todos los secretos posibles.
La revisión final debe realizarse sobre el árbol y el commit exactos que se
publiquen. El historial privado existente conserva los hallazgos indicados.

## Correcciones verificadas

| Problema | Resultado |
| --- | --- |
| Transporte autenticado de OpenRouter seguía redirecciones | Ahora las rechaza. Dos servidores loopback comprobaron que el destino no recibe la credencial ni una petición redirigida. |
| POST con JSON que no era un objeto podía devolver 500 | Arreglos, null, números y strings reciben 400. |
| Importar una carpeta inexistente o un manifiesto inválido devolvía 500 | Validación explícita y respuesta 400, sin crear un pliego ni modificar datos. |
| Espacio como tecla líder impedía seleccionar radios con teclado | Radios, casillas y botones conservan la activación nativa con Espacio. |
| Renombrar o mover una nota reconstruía el lector PDF | Los cambios de metadatos conservan el lector montado y su posición. |

También se verificaron revisiones de notas, rechazo de guardados obsoletos,
borrado sin resurrección por autoguardado, separación entre pliegos, privacidad
de claves en exportaciones y rechazo de rutas y enlaces simbólicos en respaldos.

## Pruebas y límites

| Comprobación | Resultado |
| --- | --- |
| Suite Python en 3.11.17 | 104 pruebas, sin fallos ni omisiones |
| Suite Python en 3.12.15 | 104 pruebas, sin fallos ni omisiones |
| Suite Python en 3.14 | 104 pruebas, sin fallos ni omisiones |
| MCP stdio en Python 3.11 y 3.12 | Privacidad, paginado, validación, borradores y handshake actual/legacy: correctos |
| Navegador Chromium con Playwright 1.58.2 | 14/14 recorridos correctos desde la distribución filtrada; escritorio y viewport móvil |
| Caja negra HTTP independiente, antes de correcciones | 13 checks correctos, 1 fallo de importación confirmado y 1 comprobación de Tailscale real sin ejecutar |
| Repetición de caja negra sobre el candidato corregido | 9/9 checks correctos; incluye el rechazo de importaciones inválidas |
| npm audit, runner y editor | Sin avisos conocidos reportados |
| pip-audit, 29 dependencias instaladas del entorno de autoría | Sin avisos conocidos reportados |
| PDF.js 6.4.299 y Marked 17.0.1 vendorizados | Sin avisos conocidos en el registro npm; 204 archivos PDF.js y 2 Marked coinciden byte a byte con sus paquetes oficiales. El SHA-256 de vendor.json coincide con el archivo oficial descargado. |
| Sintaxis y enlaces locales de documentación distribuible | Verificados |

Los mocks del tutor verifican contratos del software; no acreditan la calidad
semántica de un modelo ni de sus evaluaciones. No se hicieron llamadas reales
al tutor durante esas pruebas. Tailscale Serve/Funnel reales, Firefox, Safari,
lectores de pantalla y una auditoría WCAG completa no se ejercieron. Sí se
probaron rechazos HTTP de Host, Origin, identidad remota e indicador Funnel.
GitHub Actions queda preparado con versiones y SHA fijados, pero su ejecución
en GitHub requiere publicar el árbol revisado.

La última corrida de Python 3.11/3.12, del MCP y de los 14 recorridos de navegador
se ejecutó desde un candidato sin los cursos ni documentos privados. Los cambios
posteriores del paquete final se limitan a documentación de resultados y decisiones;
el código se compara por SHA-256 con el candidato probado.

## Agentes externos

Se intentaron tres trabajos con el proveedor configurado, FreeLLMAPI y
`mistral-small-4`, sobre una copia previamente filtrada. Los tres terminaron
con HTTP 503 antes de producir una auditoría. **No hay una auditoría externa
completada ni resultados externos de pruebas que atribuir a esos intentos.**
La alternativa ejecutada fue una revisión distribuida entre agentes locales,
incluida una ronda HTTP con expectativas escritas antes de inspeccionar código.
No se cambió automáticamente a otro proveedor al fallar el configurado.

## Licencia y contribuciones

La licencia elegida es [Apache-2.0](../LICENSE). Permite uso comercial bajo sus
condiciones y también permite que terceros creen productos comerciales.
Aceptar contribuciones bajo Apache-2.0 con [DCO](../CONTRIBUTING.md) no transfiere
su titularidad ni da exclusividad comercial al mantenedor. Las dependencias
conservan sus licencias y avisos en [NOTICE](../NOTICE).

Los reportes privados de vulnerabilidades de GitHub se habilitaron y la API
confirmó `enabled: true`. No se envió un reporte de prueba a otras personas.
Antes de anunciar la release falta confirmar la titularidad de los archivos
incluidos, revisar el tutorial y su enlace de video, ejecutar CI sobre el árbol
de release publicado y elegir
versión/fecha y notas finales. Los cursos y materiales privados excluidos no
necesitan publicarse para liberar el programa.


## Actualización del candidato · 15 de octubre de 2026

Esta ronda prepara la candidata `0.1.0`; no crea un tag ni publica. Se conservaron los datos, los cambios locales previos y el historial real.

- Python 3.14: 104 pruebas correctas, sin omisiones, usando un entorno de autoría temporal con `requirements-author.txt`. La primera corrida sin ese entorno omitió la prueba de extracción PDF; se repitió con la dependencia disponible.
- MCP stdio: integración actual y handshake legacy correctos con base temporal.
- Chromium: 14/14 recorridos correctos en una sola corrida desde el candidato filtrado. Se usó GPU desactivada, porque el navegador se cerraba incluso al abrir una página vacía con GPU habilitada en este entorno. No se atribuyen esos cierres al programa. El recorrido de contexto que había agotado el tiempo pasó por separado y en la corrida final.
- Se corrigieron dos expectativas antiguas de los recorridos: las consultas del PDF pertenecen a su propio apunte y no deben absorber las del apunte de texto; reabrir el PDF conserva su última página. Las pruebas comprueban además la conservación del texto, los IDs y los historiales originales.
- Se observó el proceso local en `127.0.0.1:8765`. No se pudieron consultar Serve y Funnel reales porque no hay CLI Tailscale en el entorno. Esa verificación sigue pendiente.
- El tutorial `1.0.2` explica que la clave se guarda en la instalación local y queda fuera de los respaldos de pliegos. La guía es autosuficiente y presenta el video como complemento, sin garantizar contenido no inspeccionado. Se conservaron todos sus IDs.
- YouTube oEmbed devolvió el título `glosa demo` y el canal `agusbpl` para el enlace del tutorial. Es una comprobación de metadatos: no acredita el contenido completo, su accesibilidad ni derechos de publicación.

### Revisión delegada del PDF

Antigravity trabajó en una copia filtrada: primero con el modelo configurado y luego, a pedido del responsable, con Sonnet 4.6. La primera ejecución agotó cuota. Sonnet propuso cambios en contadores y temporizadores de carga y repintado, pero no pudo ejecutar pruebas con la terminal restringida. Tampoco pudo escribir su informe en la ruta solicitada por una restricción de artefactos de la herramienta; se conservaron las trazas y la propuesta fuera de la distribución.

El coordinador revisó el parche y la prueba propuesta. La fixture de esa prueba invocaba un método inexistente y usaba un archivo temporal global; se corrigió únicamente en una copia de verificación. La prueba resultante **también pasa con el código original**, por lo que no demuestra que el parche resuelva el fallo. Un probe independiente de 21 tamaños de ventana con PDF sintético tampoco reprodujo oscilación. **El parche no se integró y el fallo visual reportado sigue abierto.** Antes de publicar, falta reproducirlo y corregirlo o aceptar expresamente esta limitación.

### Delegación a OpenCode

El responsable indicó DeepSeek V4 Flash de Inkstone y confirmó que dispone de dos cuentas. El identificador de la configuración, `deepseek-v4-flash`, fue rechazado por TokenPlan. El catálogo autenticado de ambas cuentas anunció `deepseek-v4-flash-0731`; con ese identificador una cuenta indicó cuota agotada y la segunda permitió ejecutar el encargo. La consulta del catálogo manejó las credenciales localmente y no las imprimió ni las envió a los agentes.

DeepSeek entregó la revisión de las cuatro lecciones y sus rúbricas en un encargo acotado. El coordinador contrastó y ajustó fuentes, el alcance del atajo `/` y criterios para aceptar rutas alternativas y decisiones de privacidad justificadas. La entrega integrada está en [revision-tutorial.md](revision-tutorial.md); la independencia respecto de la autoría original no está acreditada. Las comprobaciones de software del coordinador no se atribuyen a OpenCode ni acreditan calidad de un tutor real.

## Cierre autorizado · 15 de octubre de 2026

La persona responsable confirmó que hizo el video del tutorial y pidió completar
la release y tratar el historial. Se preparó y verificó un Git bundle completo
en una carpeta privada ignorada; también se respaldaron el diff y los archivos
sin seguimiento. La publicación usará una historia nueva desde el árbol filtrado,
sin unir los diez commits anteriores. La revisión actual de los correos de autor
y committer de esos diez commits muestra únicamente el correo público noreply;
la afirmación inicial sobre correos reales no se sostiene para esos metadatos.
Los archivos personales y rutas históricas siguen justificando el filtrado.

Se reprodujo la oscilación del PDF mostrando barras de desplazamiento clásicas.
La página ajustada al ancho hacía aparecer y desaparecer la barra vertical,
cambiando a su vez el ancho útil. La corrección reserva el espacio mediante
`scrollbar-gutter: stable`. La nueva prueba falla antes de la corrección y pasa
después. Incluye 1100×933 y los tamaños 1366×768 y 1366×650; la resolución eDP
real se consultó con `xrandr`. Ver [el detalle](pendientes-interfaz.md).

No hay instalación local de Tailscale, socket o unidad de Serve/Funnel que se
pueda consultar, ni listener local en 8765/443 durante la inspección. Esta
comprobación no acredita acceso remoto de otro equipo. Se mantiene loopback
como despliegue predeterminado y Serve privado como opción por configurar.

La sustitución de la rama se verificará desde un clon nuevo y con las referencias
de GitHub. No elimina copias anteriores ni acredita que GitHub haya purgado
objetos no referenciados; una solicitud de purga requiere GitHub Support.
