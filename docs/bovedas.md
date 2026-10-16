# Margen · la bóveda visible con todas tus materias

Glosa guarda tu estudio en un **Margen**: una carpeta visible de esta computadora
que contiene **todas tus materias**. Cada materia es un **pliego**: una subcarpeta
con sus cursos, PDFs, apuntes, historial y conversación con el tutor. Los pliegos
no se mezclan entre sí, pero el Margen es uno solo: no hay una «bóveda» por
materia, hay un Margen con pliegos adentro.

```
~/Margen/                     ← el Margen (bóveda visible, una sola)
├── Análisis Numérico/        ← un pliego (materia)
│   ├── pliego.json
│   ├── learning/learning.sqlite3
│   ├── assets/               ← sources/, documents/, .md_cache/
│   └── Apuntes/              ← apuntes originales en Markdown
├── Sistemas/
│   └── …
└── Biblioteca local/         ← tu biblioteca de siempre, ya trasladada (opcional)
```

## Qué es un pliego en el disco

Cada pliego es una subcarpeta del Margen con esta forma:

```
<materia>/pliego.json          # identidad: formato, versión, ID y nombre visible
<materia>/learning/learning.sqlite3  # cursos, apuntes, PDFs registrados, historial,
                                     # conversación, calendario y ajustes
<materia>/assets/              # archivos reales: sources/, documents/, .md_cache/
<materia>/Apuntes/             # apuntes originales editables en Markdown
```

- El **Margen** se resuelve en este orden: `GLOSA_MARGEN_DIR` (variable de
  entorno, tiene prioridad y bloquea el cambio) → la ruta guardada en
  `margen.json` (elegida desde la pantalla) → `~/Margen` por defecto, que se crea
  al usarse. En las pruebas el valor por defecto se aísla con un `HOME` temporal.
- El **ID** del pliego (`pliego-…`, `room-…`, `local`) vive en `pliego.json` y no
  cambia aunque la carpeta se mueva o se renombre: el descubrimiento escanea el
  Margen en cada consulta.
- El nombre de la carpeta es **humano** y se deriva del título del pliego. Un
  título es un dato del usuario: nunca se usa para escapar del Margen (se quitan
  separadores, se normaliza Unicode, se limitan caracteres reservados).
- El descubrimiento también revisa la carpeta legada `<datos>/margen`, para que
  los pliegos previos a este cambio no desaparezcan, y deduplica por ruta física.
- La **Biblioteca local** es tu espacio de siempre, con su `id='local'`. Sigue en
  la carpeta de datos de la aplicación hasta que decidas **trasladarla** a un
  pliego visible del Margen (ver más abajo). **Primer trazo** (el tutorial) es
  una demostración aparte que no toca tus cursos ni tu historial.

## Qué hace la interfaz de Margen

Al pulsar GLOSA (o `g o`) se abre el diálogo de Margen, que muestra:

1. **Tu Margen abierto**: nombre, ruta absoluta de la carpeta (con botón de
   «Copiar ruta»), resumen de contenido y última modificación. Si lo abierto es
   la Biblioteca local o el tutorial, explica qué es y qué no toca.
2. **Tus pliegos**: una fila por pliego con su ruta, chips (cursos, fuentes,
   apuntes, mensajes con el tutor, registros y tamaño) y el botón «Renombrar».
   Elegir una fila la abre: se guardan los apuntes y el tiempo pendientes y la
   página recarga dentro del pliego nuevo. Los IDs no cambian.
3. **Crear un pliego nuevo**: una subcarpeta nueva dentro del Margen con base
   vacía, que se abre al terminar.
4. **Dónde está tu Margen**: la ruta, de dónde sale (entorno, ajustes o valor por
   defecto) y cuántos pliegos se encontraron. Cambiar la carpeta no mueve
   archivos: solo le dice a Glosa dónde buscarlos.
5. **Copias detectadas** e **Importar una copia**: carpetas con forma de respaldo
   y la importación por ZIP o carpeta; siempre crean un pliego **nuevo** con una
   copia, nunca sincronizan ni sobrescriben.
6. **Exportar este pliego**: ZIP verificado (con `manifest.json` y hashes) sobre
   una lectura consistente de la base, con PDFs, apuntes originales y vistas
   legibles.

El resumen de contenido lo calcula `rooms.inventory()` abriendo cada
`learning.sqlite3` en **modo solo lectura** (`file:…?mode=ro`): no escribe, no
crea `‑wal`/`‑shm` y degrada a «Contenido no disponible» si una base está ocupada
o dañada. La apertura de pliego usa `inventory(details=False)` para no pagar ese
costo en cada request, y `margen(create=False)`/`inventory(create=False)`
permiten describir el Margen sin crear carpetas (plan/dry-run).

## Renombrar un pliego

`rooms.rename(data, root, room_id, title)` cambia el nombre visible **y mueve la
carpeta** a un nombre humano derivado del título, de forma atómica (`rename` en
el mismo sistema de archivos): actualiza `pliego.json` y el registro `rooms.json`
si el pliego está registrado, y **no toca el ID, el contenido ni el historial**.
El navegador guarda los apuntes pendientes antes de pedir el cambio. Si el
sistema de archivos rechaza el movimiento, se restaura el título anterior y no
queda una carpeta huérfana. Si una petición concurrente vuelve a crear la carpeta
vieja, su ruta se registra en `mover-restos.json` y se muestra como advertencia
hasta que se resuelva. Rechaza títulos inválidos, la Biblioteca local, el
tutorial y pliegos inexistentes. Se prueba en `tests/test_rooms.py` y
`tests/browser_rooms.cjs`.

## Trasladar la Biblioteca local al Margen

La Biblioteca local conserva su `id='local'`. El **script de migración** copia su
base (con la API de respaldo de SQLite), sus PDFs, sus cachés y sus apuntes a un
pliego visible del Margen y escribe un marcador `local-migrated.json` con la
huella (`bytes`, `mtimeNs`) de la base original. El marcador solo se acepta si la
base original **no cambió** después de la copia: así nunca se activa una copia
vieja. El original **no se borra** automáticamente. Una vez trasladada, el alias
de la Biblioteca local **ya está conectado**: el servidor resuelve `id='local'`
hacia la bóveda del Margen mientras el marcador `local-migrated.json` siga
siendo confiable. Si el original cambia después, `rooms.local_scope()` lo detecta
y avisa, y nunca se usa una copia vieja. El detalle de dónde queda cada archivo
está en [almacenamiento](almacenamiento.md) y el ciclo de los pliegos en
[salas-y-continuacion](salas-y-continuacion.md).

## Migración de todos los pliegos a un Margen visible

`scripts/migrate_vaults.py` reúne **todos** los pliegos —incluidos los legados sin
`pliego.json` y la Biblioteca local— en un Margen con nombres humanos, sin
fusionar bases ni cambiar IDs:

```bash
# 1) Describir sin tocar nada (solo lectura, no crea el Margen):
python3 scripts/migrate_vaults.py plan
python3 scripts/migrate_vaults.py dry-run

# 2) Aplicar con un respaldo verificable FUERA del repositorio:
python3 scripts/migrate_vaults.py apply \
  --data ~/.local/share/glosa --target ~/Margen --respaldo /ruta/privada/respaldo

# 3) Comprobar el resultado:
python3 scripts/migrate_vaults.py verify --target ~/Margen

# Recuperar una corrida interrumpida (limpia solo restos propios):
python3 scripts/migrate_vaults.py apply --recuperar …
```

Garantías del script:

- `plan`/`dry-run` son de solo lectura: no crean el Margen, ni bases, ni carpetas.
- `apply` exige `--respaldo` fuera del repositorio, exporta cada pliego con
  `export_room` y lo verifica con `verify_bundle` (sin claves de API).
- Los traslados son atómicos en el mismo sistema de archivos; entre sistemas, se
  copia a una carpeta temporal oculta, se verifica por hash y recién entonces se
  borra el origen.
- **Metadata portable antes de mover**: un pliego legado que solo traía
  `assets`+`learning` recibe su `pliego.json`; sus apuntes se reubican en
  `<pliego>/Apuntes` y los Markdown que ya existían se preservan byte a byte.
- **Huella de contenido**: antes de mover se capturan IDs y `sha256` de cursos,
  eventos, notas, versiones, documentos, calendario y ajustes, y el `sha256` de
  cada archivo de `assets`; se vuelven a comprobar después. Los conteos por sí
  solos no alcanzan.
- **Idempotente y recuperable**: bloqueo exclusivo (`O_EXCL`), diario por pliego
  y `--recuperar` que solo limpia restos propios. Un pliego ya movido se
  redescubre por su `pliego.json`, nunca por el registro viejo, así que un corte
  entre el movimiento y la actualización del registro no duplica nada.
- Una carpeta destino con **otro** contenido aborta ese pliego sin mezclar; dos
  pliegos con el mismo título se resuelven anexando ` (2)`, ` (3)`… y conservan
  su ID.

## Garantías y límites

- Cambiar de pliego nunca fusiona ni borra datos: cada pliego tiene su base y su
  carpeta. IDs iguales en pliegos distintos son independientes.
- Importar un respaldo o un ZIP crea un pliego **nuevo** con IDs preservados; el
  original queda intacto.
- No hay sincronización entre pliegos ni entre procesos: cada pliego se abre en
  la aplicación que lo sirve. Git o el ZIP siguen siendo respaldos manuales
  ([salas-y-continuacion](salas-y-continuacion.md)).
- Los apuntes Markdown son el original editable; la base los indexa. Una edición
  externa se adopta al reconciliar y la migración no la pisa
  ([almacenamiento](almacenamiento.md)).
- La verificación de la plataforma es mecánica; la comprensión del usuario sobre
  su propio material sigue siendo suya y del flujo de
  [evaluación rigurosa](evaluacion-rigurosa.md).

## Cómo se prueba

- `python3 -m unittest tests.test_rooms tests.test_margen tests.test_migracion_bovedas`:
  inventario en solo lectura (sin archivos de lado, degradación ante base
  ilegible), nombres humanos y únicos, rename que mueve la carpeta y conserva
  ID/historial, pliegos legados solo registrados, alias local con detección de
  cambio, y migración `plan` (solo lectura), aplique con respaldo verificado,
  idempotencia, colisiones y recuperación. Todo con `HOME`/`GLOSA_MARGEN_DIR`
  temporales; nunca se escribe en el `~/Margen` real.
- `npm run test:browser -- browser_rooms.cjs browser_onboarding.cjs`: recorrido
  real de navegador con `HOME` temporal — explicación visible, tarjeta con ruta y
  contenido, renombrado que mueve la carpeta y conserva el ID, aislamiento de
  notas con IDs iguales, exportación acotada al pliego abierto y pliego nuevo
  descubierto tras mover su carpeta.
