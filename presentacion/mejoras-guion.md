# Glosa · Un estudio que conserva el hilo

Abrí **glosa-interactiva.html** directamente en el navegador: incluye todo en un único archivo.
También podés abrir **mejoras.html**, que carga los scripts locales por separado. Esta es la presentación
completa de las mejoras recientes, con ocho escenas animadas y 25 pasos.
Duración sugerida: 6–9 minutos, con avance manual.

La escena inicial de lectura sigue disponible en `lectura.html`; la presentación
anterior se conserva en `glosa.html`. Los archivos del nuevo recorrido son
`mejoras.html`, `mejoras.js`, `lectura-escena.js` y la copia local de GSAP en `vendor/`.
No requiere instalación, servidor ni conexión a Internet.

## Controles

- Flechas izquierda/derecha o Espacio: recorrer los pasos.
- Flechas arriba/abajo o controles superiores: cambiar de escena.
- I: índice. R: reiniciar escena. F: pantalla completa.
- Inicio: comienzo. Fin: cierre. Escape: cerrar un diálogo.
- Reproducir recorrido: avance automático con pausas para leer.
- Reducir movimiento: mostrar los estados sin las transiciones de la escena.
  También respeta la preferencia del sistema.

El enlace de cada paso se conserva en la dirección y permite abrirlo directamente.
Los controles de teclado respetan los botones que tienen el foco.

## Relato

### 1. Tu Margen

Presentá Margen como una carpeta visible que reúne las materias. Cada pliego
conserva sus fuentes, apuntes, cursos e historial. Los nombres de materias y
cantidades del diagrama son ilustrativos. Pulsá una materia para abrir el
esquema de su contenido. Podés cambiar entre materias y renombrar un pliego.

### 2. Preparar una materia

Mostrá el flujo carpeta → encargo → agente → pliego. En Glosa, el formulario
permite elegir la carpeta y agregar examen, temario y disponibilidad. Genera un
texto editable para copiar, no ejecuta al agente. El agente redacta y entrega
el pliego completo dentro de Margen; requiere revisión humana de fuentes,
actividades y rúbricas. No prometas preparación automática sin intervención.

### 3. Leer y anotar

Recorré la escena de lectura: fragmento, resaltado, elaboración propia y regreso
a la fuente. Mencioná los cuatro colores y la posibilidad de quitar una marca
conservando historial. La referencia del apunte es interactiva.

### 4. Conectar conceptos

Mostrá enlaces, referencias inversas y menciones en clases y ejercicios. La
ficha agrega definición propia, ejemplo, contraejemplo, fuente y pregunta.
Completarla organiza el estudio; no demuestra comprensión por sí solo.

### 5. Errores y repaso

Contá cómo registrar un error y su corrección sirve para retomarlo. Las propiedades
permiten agrupar por materia, unidad, fecha de parcial y necesidad de practicar.
El ejemplo del gráfico es ilustrativo; no es una respuesta de un estudiante.

### 6. Tutor y acompañamiento

Explicá que el tutor es opcional y trabaja con el contexto seleccionado. La
integración externa permite usar el modelo del programa externo y registrar
la conversación. Las condiciones y costos dependen del proveedor.
Pulsá los modos para mostrar sus diferencias. Auto explica sus decisiones con
fechas y evidencia disponibles. La ayuda recibida no acredita dominio independiente.

### 7. Plan de parciales

Varias materias comparten una sola disponibilidad. Pulsá «Cambiar prioridad»:
los 120 minutos ilustrativos se reparten de otra manera. En la aplicación las
prioridades consideran cercanía, preparación y dificultades; faltantes y
postergaciones deben quedar visibles. Estos minutos son un ejemplo de la
presentación, no un plan real ni una recomendación personal.

### 8. Conservar tu trabajo

Mostrá que los apuntes Markdown pueden editarse por fuera de Glosa, con revisiones
y conflictos visibles. Los respaldos reúnen el pliego y se importan como una
copia nueva. Antes de compartirlos conviene revisar sus documentos e historial.
Cerrá con el recorrido completo: preparar, leer, conectar, practicar y retomar.

## Alcance editorial

Contenido basado en los cambios recientes del 16/10/2026 y el árbol de trabajo
posterior: README, documentación de bóvedas, autoría, herramientas de estudio,
tutor externo y modos del tutor. No se presentan como implementadas las ideas
pendientes de voz natural o seguimiento automático de texto.
Todos los diagramas son explicativos y no usan datos privados ni escriben en Glosa.

Para regenerar el HTML autónomo después de editar las fuentes: `python3 presentacion/compilar.py`.

## Dirección visual revisada

La tutora ahora es **Glosa**, una mascota de papel en tres versiones ilustrativas:
Flexible con linterna, Estricta con lupa y Extrema de expedición. Sus preguntas
son ejemplos de cada modo, no evaluaciones reales. Pulsar una versión cambia el
personaje, el ambiente y su intervención. La ilustración fue generada con la
herramienta integrada image_gen; los archivos y el prompt están en `ilustraciones/`.

El recorrido alterna composición lateral, texto a la derecha, una constelación
sobre fondo oscuro, acentos de dibujo a mano y un cierre con un hilo que conecta
las etapas. La apertura de video opcional tiene su propuesta en `video-apertura.md`.
Las fuentes nuevas son `escenografia.js` y `escenografia.css`; `compilar.py` incorpora
todo, incluida la mascota, en el único archivo `glosa-interactiva.html`.

## Apertura integrada con video

El clip aportado por el usuario se incorporó como apertura a pantalla completa,
detenida en el primer fotograma, sin títulos superpuestos. La tecla → o el
botón → inicia el video; al terminar sus 8 segundos pasa al recorrido. Durante
la reproducción se puede pausar o pulsar → para saltar al recorrido. Se puede
volver a verlo con «Apertura» en el encabezado.
Reabrir la apertura conserva la escena actual. Los enlaces directos a escenas
omiten la apertura. En movimiento reducido se muestra una imagen estática.

La copia `video/glosa-apertura-sin-audio.mp4` conserva el video H.264 original y
**no contiene pista de audio** (retirada con FFmpeg, sin recodificar el video).
El MP4 original del directorio Downloads no fue modificado. El HTML autónomo
incluye tanto el clip como el fotograma estático; funciona sin archivos auxiliares.
