# Almacenamiento de apuntes · Markdown original

Los apuntes viven como archivos `.md` legibles y editables también con Obsidian,
Vim o cualquier editor. SQLite es un índice: guarda revisiones efectivas,
conversación del tutor y evaluaciones, pero **no** es la fuente de verdad del
texto. Nunca se pisa una edición externa en silencio.

## Dónde quedan los archivos

- En una bóveda (`learning.sqlite3` dentro de `learning/` con `pliego.json` al
  lado): `<raíz del pliego>/Apuntes/`.
- En la biblioteca local aún no trasladada: `<datos>/Apuntes/`.

El nombre de archivo y las carpetas son humanos y seguros: `Materia / Unidad /
Título.md`. Los caracteres no permitidos, los intentos de salir de la carpeta
(`..`) y los enlaces simbólicos se descartan. Las carpetas ocultas (`.`),
`.glosa-eliminados` y `.glosa-conflictos` no se recorren.

## Formato

```markdown
---
glosa_schema: 1
glosa_id: 3d05e432-…        # ID estable: sobrevive a renombres y movimientos
glosa_revision: 2
glosa_sync: <sha256>        # huella del contenido+metadata (sin la revisión)
title: Clase sin filmina
folder: Análisis/Unidad 3
shared: true
documentId: fixture-pdf
page: 1
writingScope: page
contentFormat: body
createdAt: "2026-10-16T17:42:37+00:00"
updatedAt: "2026-10-16T17:42:37+00:00"
---

<!-- glosa:general -->
Texto del apunte general, tal cual lo escribís.
<!-- /glosa:general -->

<!-- glosa:page id="fixture-pdf" page="1" -->
Notas de la página 1 del PDF, visibles y editables.
<!-- /glosa:page -->

<!-- glosa:data
{"anchors": [...], "study": {...}}
-->
```

- El **texto** del apunte general y de cada página está en el cuerpo, visible al
  renderizar y editable a mano. Los delimitadores son comentarios HTML.
- `pageNotes`, las anclas y la metadata de estudio (`study`) sobreviven el viaje
  de ida y vuelta sin pérdida. Las anclas y `study` se guardan como estructura
  auxiliar en el comentario final.
- Las claves de frontmatter que Glosa no administra (`tags`, `cssclasses`, …) se
  conservan tal cual.
- En un archivo de Windows (BOM, CRLF) el texto se lee sin cambiar lo que se ve.

## Cómo se sincroniza

Cada vez que se lee el estado, Glosa compara los archivos con el índice:

- **Edición externa**: el archivo gana. El contenido cambia y sube la revisión;
  la versión anterior queda en el historial.
- **Archivo movido o renombrado a mano**: se reconoce por su `glosa_id`, se
  adopta la ruta nueva y se conserva el ID. No se duplica.
- **Archivo borrado a mano**: la nota pasa a *eliminados*; no se recrea el
  archivo. El texto que había queda en el historial.
- **Archivo roto** (formato que Glosa no entiende): se avisa; el archivo no se
  toca ni se sobrescribe.
- **Dos archivos con el mismo `glosa_id`**: se avisa y no se adopta ninguno para
  no pisar texto.
- **Nota escrita a mano sin `glosa_id`**: se adopta de forma transparente con un
  ID propio, sin modificar el archivo.

Los avisos aparecen en `library.noteWarnings` (visibles en la interfaz).

## Guardar sin perder nada

- El guardado es **atómico** (archivo temporal + reemplazo) y escribe primero el
  archivo y después la fila. Si el proceso se corta en el medio, la próxima
  lectura adopta el archivo sin perder texto.
- Antes de escribir se sincroniza el apunte. Si el archivo cambió afuera, el
  guardado se rechaza con un mensaje explícito, el **borrador local se conserva**
  y hay que recargar para guardar sobre la versión vigente.
- Si en la ventana entre la lectura y el reemplazo un editor cambia el archivo,
  Glosa lo detecta, no lo sobrescribe y guarda tu borrador en
  `Apuntes/.glosa-conflictos/`.
- Eliminar un apunte mueve su archivo a `Apuntes/.glosa-eliminados/` (fuera de la
  vista), nunca lo borra sin rastro.
- Al reabrir la ventana o volver a la pestaña, Glosa relee el estado. Sin cambios
  locales recarga el apunte; con cambios locales conserva el borrador y avisa.
- El snapshot y respaldo JSON ya incluyen el payload crudo de modos del tutor
  (`tutorModes`) vía `export_payload`/`import_payload`, junto con cursos,
  calendario, ajustes y biblioteca.

## Migración

`Library.migrate_notes_to_files(dry_run=...)` exporta a archivos los apuntes que
solo vivían en SQLite. Es idempotente, y en una segunda pasada **importa** las
ediciones externas en lugar de reexportar la base sobre el archivo. La migración
real la aplica el orquestador sobre copias verificadas; estas pruebas no tocan
datos reales.

## Límites conocidos

- El marcador de cierre dentro del texto de una página (o del general) cortaría la
  sección; es improbable y se documenta.
- La guarda de escritura evita la ventana habitual de conflicto, pero no es un
  compare-and-swap perfecto frente a editores que escriben en el mismo instante.
- La interfaz de estudio usa la misma API de notas; una propiedad elegida sobre
  una versión que cambió afuera queda pendiente y se avisa.
