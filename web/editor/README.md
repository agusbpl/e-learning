# Editor del apunte

CodeMirror edita el Markdown original y aplica formato con decoraciones. `@replit/codemirror-vim` aporta el motor Vim y se activa con el perfil `modal` (Vim integrado). La misma instancia de motor se usa en respuestas y mensajes; los campos nativos conservan valores, validación y handlers de borrador. La aplicación captura Espacio como tecla líder solo en NORMAL. :w guarda el apunte; :q sale del campo. La edición no convierte HTML a Markdown ni modifica el documento al entrar o salir de Foco. Los delimitadores del fragmento activo se muestran para poder editarlos; el texto conserva su estilo. Las tablas, imágenes y bloques de código se muestran renderizados fuera del fragmento activo.

El navegador carga `../live-markdown.js`, incluido en el repositorio. No descarga paquetes ni usa un CDN al abrir un apunte. Para reconstruir ese archivo con las dependencias fijadas en `package-lock.json`:

```sh
cd web/editor
npm ci
npm run build
```

`THIRD_PARTY_LICENSES.txt` conserva las licencias de las dependencias. La prueba `tests/browser_note_markdown.cjs` usa una base temporal para verificar escritura en vivo, conservación exacta del texto, cursor, deshacer/rehacer, pegado, Foco, guardado y exportación.

Espacio muestra los comandos de la tecla líder fuera de Foco, sin sacar el cursor del editor. Esc cancela el prefijo. La lista visible y las acciones comparten una sola definición en `keyboard.js`. En Foco siguen funcionando los mismos atajos sin mostrar la ayuda. `v`, `V` y `Ctrl+v` seleccionan por carácter, línea y bloque; `drawSelection()` dibuja el resaltado y `allowMultipleSelections` conserva todas las filas del bloque. `y`, `d` y `c` operan sobre la selección con el motor Vim. En teoría o PDF, `v`/`V` activan la selección del navegador, los movimientos la extienden dentro del panel y `y` copia el texto.
