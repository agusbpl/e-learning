# Primera release · 0.1.0

La publicación usa exclusivamente los archivos permitidos en `release-files.json`.
Los datos de estudio, PDFs, cursos personales, bases, credenciales, respaldos,
capturas y la historia anterior quedan en la instalación privada.

## Estado del cierre · 2026-10-15

- [x] Video del tutorial: autoría confirmada por la persona responsable y autorización para continuar con la release.
- [x] Revisar el contenido distribuido: código y documentación del proyecto, tutorial propio y dependencias con sus licencias y avisos conservados en `NOTICE`.
- [x] Preparar un árbol público por lista explícita, sin `.git`, cursos personales, `output/` ni `web/media/`, con manifiesto SHA-256.
- [x] Conservar Apache-2.0 y los avisos de las dependencias vendorizadas.
- [x] Revisar semánticamente las cuatro actividades y rúbricas del tutorial según la regla de evaluación rigurosa. Ver [revision-tutorial.md](revision-tutorial.md).
- [x] Reproducir y corregir la oscilación del PDF; prueba que falla antes y pasa después. Ver [pendientes-interfaz.md](pendientes-interfaz.md).
- [x] Crear y verificar respaldo privado de la historia Git, el diff local y los archivos sin seguimiento antes de reemplazar la historia pública.
- [x] Sustituir la rama pública por una historia inicial filtrada con identidad pública; comprobar ramas, tags y clones posteriores.
- [x] Completar 104 pruebas Python sin omisiones, MCP y los 15 recorridos de navegador; repetir los recorridos desde un clon público limpio.
- [x] Completar CI sobre el commit publicado, incluyendo las correcciones surgidas en GitHub: Python 3.11/3.12, MCP y 15 recorridos Chromium.
- [x] Reportes privados de vulnerabilidades habilitados en GitHub.
- [x] Revisar el despliegue local actual: sin proceso Tailscale, CLI, socket o unidad local de Serve/Funnel disponibles. No se habilitó acceso público.

La versión se identifica por el tag `v0.1.0`. Las notas, el paquete y sus
checksums se distribuyen en [GitHub Releases](https://github.com/agusbpl/glosa/releases/tag/v0.1.0).
El tag se crea únicamente después de verificar el commit final.

Tailscale Serve real no pudo ejercerse porque este equipo no tiene la instalación
administradora. La release funciona en loopback y documenta el acceso remoto como
opcional. No se certifica una configuración de otro equipo. Antes de usar acceso
remoto, comprobar Serve privado y Funnel deshabilitado allí.

## Preparar y verificar otra distribución

```bash
python3 scripts/prepare_release.py --output /tmp/glosa-public-candidate
```

El destino debe ser nuevo y estar fuera del proyecto. El script rechaza rutas
privadas, enlaces simbólicos, patrones de credenciales conocidos y rutas del
directorio personal; no lee archivos excluidos ni copia `.git`.
`RELEASE_MANIFEST.json` registra tamaños y SHA-256. El filtro no descubre todo
secreto posible ni sustituye la revisión de permisos de terceros.

Ejecutar los controles de [desarrollo](desarrollo.md) desde el candidato, usando
bases temporales. Al publicar, revisar el commit y tag exactos: los archivos
«Source code» de GitHub salen del tag, no del paquete adjunto.

## Historia pública y copia privada

La persona responsable autorizó tratar el historial el 2026-10-15. El respaldo
privado debe conservarse fuera de cualquier distribución. La nueva historia
empieza con el árbol filtrado y usa el correo público noreply del mantenedor.
No mezclar ni volver a subir ramas antiguas; después del reemplazo, clonar de
nuevo y trasladar únicamente cambios revisados por la lista de archivos.

Reescribir la rama no retira clones descargados ni garantiza borrar objetos
no referenciados de GitHub. Para retirar datos sensibles de vistas en caché o
referencias internas, corresponde el procedimiento de
[GitHub Support](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
No se declara una purga del servidor sin confirmación de GitHub.

Los resultados y límites históricos se conservan en [auditoria-release.md](auditoria-release.md).

El clon público posterior a la sustitución no contiene los diez commits
anteriores y sus archivos coinciden con el manifiesto. La consulta directa
del SHA anterior todavía responde en GitHub: la limpieza de la rama está
comprobada, la purga de objetos del servidor no. Se preparó una solicitud
privada para GitHub Support; no se envió automáticamente.

La [corrida de CI que verificó las correcciones](https://github.com/agusbpl/glosa/actions/runs/38772511216)
completó los tres trabajos correctamente. La verificación del cierre documental detectó la misma devolución tardía de
foco en el gestor de contexto. Se corrigió también y se añadió una prueba
que falla antes y pasa después; el CI del commit final debe verificar esta
corrección antes de etiquetarlo.
El checkout de trabajo se adaptó a la historia limpia sin borrar archivos
locales. Se verificaron por SHA-256 79 archivos privados sin modificaciones;
la metadata Git anterior y los respaldos permanecen en una carpeta privada.
