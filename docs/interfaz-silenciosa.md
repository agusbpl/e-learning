# Una página, paneles a pedido

Estudiar usa la propuesta visual 2: columna de lectura centrada, tipografía serif, colores sobrios y encabezado mínimo, sin breadcrumb ni barra inferior. Los controles de teclado, enfoque y sesión están en Ajustes (`g a`); el modo actual aparece discretamente en una esquina. Las referencias y actividades siguen presentes. El índice se abre con `/` o `g l`; el tutor con `g t`. El tutor ocupa casi toda la altura disponible y arranca cerca del borde superior; en celular usa la altura completa. El historial desplaza su propio contenido. `Esc` cierra el panel y conserva el borrador del chat. Foco (`z`) oculta también la entrada del tutor, que sigue disponible por comando.

`g e` lleva a Estudiar, `g n` a Notas, `g c` al Cuaderno y `g p` al Plan. `:` abre comandos; `f` permite activar los controles visibles con letras. El perfil Vimium deja los atajos a la extensión. Foco y perfil de teclado conservan su configuración global en el servidor.

## Tres vistas del mismo apunte

En Notas, los atajos y `:` permiten alternar:

- **Apunte (`m a`)**: página centrada para escribir. El PDF adjunto y las referencias permanecen vinculados, aunque la fuente no esté desplegada.
- **Fuente al lado (`m f`)**: PDF a la izquierda y apunte a la derecha. Es la vista automática al adjuntar o elegir una fuente.
- **Lectura con margen (`m l`)**: fuente amplia y comentarios de la página actual en el margen. Los textos por página se muestran en celdas; `i` escribe en la celda activa. Cambiar de página cambia los comentarios visibles; todos permanecen en las otras vistas y exportaciones.

Fuente al lado y Lectura con margen requieren un PDF. La vista elegida se recuerda por apunte en ese navegador; no cambia el contenido compartido entre dispositivos. El selector de apuntes se abre con `/` y se cierra con `Esc`. `Ctrl+Espacio h/l` cambia de panel, `[` y `]` cambian la página del PDF. `a` anota una selección o la página completa; los comentarios admiten edición y borrado. `Ctrl+s` guarda el apunte.

En pantallas pequeñas fuente y apunte se apilan. Los modos de escritura NORMAL/INSERTAR/VISUAL son independientes de las tres vistas de Notas.

Los conceptos generados están en `/designs/notas.html`, con imágenes y prompts originales en `output/disenos/`. Las capturas de implementación en `output/qa/` usan una base temporal de pruebas, sin alterar el historial del estudiante.

## Escribir por página o por separado

Los atajos y **Propiedades del apunte** en `:` permiten elegir **Por página del PDF** (`m p`) o **Apunte general** (`m g`). Cada página de cada PDF tiene su propia celda; `[` / `]` lleva a la celda correspondiente y entrar en una celda sincroniza el PDF. `j/k` en NORMAL dentro del apunte recorre celdas e `i` escribe. `g b` abre o crea una celda por número. Escribir `#29` en una línea muestra la página; Enter pasa a su celda sin sobrescribir las notas existentes. `#1` siempre está presente. Sólo se despliegan páginas con notas o abiertas, sin crear cientos de celdas vacías para un libro. **Markdown completo** despliega el texto continuo para pegar o reorganizarlo; el cursor controla la página del lector sin reescribir la entrada. También funciona en la vista Apunte, con el PDF oculto. El texto general se conserva por separado: alternar organización no lo copia ni lo borra. Al adjuntar una fuente se activa la escritura por página; los apuntes anteriores siguen en Apunte general.

Cada comentario tiene otro selector: **Página del PDF** o **Independiente del PDF**. Los comentarios de página se muestran al leer esa página, en las tres vistas; los independientes aparecen en su propia sección, al pasar de página y también sin PDF. Desde Editar se puede cambiar el vínculo. Si el comentario partió de un fragmento de fuente, conserva la cita y su referencia aunque pase a ser independiente.

El guardado, versiones, exportaciones JSON/Markdown y contexto del agente autor incluyen textos por página y comentarios independientes. Las notas antiguas se interpretan como apuntes generales; las referencias antiguas siguen vinculadas a sus páginas. Los campos aditivos son `writingScope`, `pageNotes` (documento → número de página → texto) y `scope` en cada comentario. Los textos por página se guardan en el servidor, no sólo en el navegador.

## Preguntar al tutor mientras escribís

**Preguntar al tutor** bajo el editor consulta sobre el texto seleccionado, o todo el texto visible si no hay selección. **Guardar y preguntar** en una anotación guarda el comentario antes de enviarlo y muestra la respuesta en el mismo diálogo. `Ctrl+Shift+Enter` activa estas acciones mientras escribís; `Ctrl+Enter` sigue guardando el comentario sin consultar. El atajo de consulta también está disponible con perfil Vimium, sin capturar sus letras. `g t` en Notas abre una pregunta libre sin cambiar a Estudiar ni enviar nada por sí solo.

La consulta es opcional: escribir, guardar o cambiar de página nunca llama al modelo. Usa el tutor gratuito conectado en Ajustes. Se envían la duda, el texto pertinente del apunte o comentario y el texto extraído de su página PDF si tiene una referencia. Un apunte general sin referencia no envía automáticamente el PDF ni los textos de otras páginas. No se envían otras notas, cursos o anotaciones privadas. Pedir ayuda sobre una nota privada permite enviar esa consulta puntual sin cambiar su opción de compartir con el autor externo.

El historial reciente del tutor se limita a seis consultas respondidas del mismo apunte, comentario y página. Cada intercambio conserva una copia del contexto y la revisión original; una respuesta tardía no cambia de página ni sobrescribe lo que estés escribiendo. Las consultas pendientes o fallidas conservan la duda, permiten reintentar y aparecen en **Consultas del apunte**. Reintentar es una acción explícita nueva; una solicitud repetida con el mismo ID no dispara otra llamada.

Los intercambios están en `library.noteTutor` del respaldo JSON, en el Markdown completo y en el Markdown del apunte. El MCP incluye consultas únicamente de apuntes actualmente compartidos, filtradas por carpeta. La interfaz avisa que compartir el apunte también comparte sus consultas. Las ayudas nunca generan evaluaciones de dominio ni aprueban lecciones. No se hace OCR ni se garantiza la exactitud de una respuesta del modelo.

Las respuestas JSON del tutor de estudio se separan del mensaje visible. Objetos de criterio en `evidence` se normalizan y siguen pasando por el control de evidencia. Una respuesta truncada o inválida puede conservar su texto recuperable, pero no genera una evaluación ni acredita dominio. El registro original se conserva para auditarlo; los mensajes antiguos también se decodifican para mostrarlos sin sobrescribir el historial.

Anotar una selección se activa solo al seleccionar texto de teoría o usar el comando correspondiente. Los clics sin selección no muestran avisos; el tutor, el índice y los diálogos abiertos no disparan anotaciones de la teoría del fondo. La ayuda de teclado sigue disponible con `?`.

Las opciones múltiples no muestran el círculo del radio: la opción elegida se indica con fondo y texto destacado. Los controles nativos conservan accesibilidad, foco, selección con Space/flechas y validación. **Deshacer revisión** está en el pie de una lección marcada y su fila del Plan. Conserva respuestas, anotaciones y evaluaciones; registra `self_review_cancel` con los IDs de marcas canceladas. Una marca posterior vuelve a estar activa. Deshacer no significa acreditar ni borrar una evaluación del tutor.
