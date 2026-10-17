# Referencia local: vista previa de notas de Obsidian

Inspección estática del paquete instalado `/usr/lib/obsidian/obsidian.asar`. No se ejecutó Obsidian ni se abrieron bóvedas.

REA: `ev_7321f17cd9e28e51b156366ef9f0c78390cb8a17444de27b923823299eb136dc`, resumen `ev_c73b9af579fe8f68765bd2becc9abdff4ae2bc4d8e15e9bfdd424e2f9562bf26`. El análisis general agotó 30 segundos y su cobertura es parcial; no acredita comportamiento en ejecución.

Comprobación focalizada de los bytes de `app.js` extraídos directamente del ASAR (SHA-256 958ce57fe22f87fdf121546e46dfccd9c8ee971ce3fd8f801d60d4ece39a2df9). El código contiene manejadores de entrada/salida del puntero tanto en el enlace como en el popover, y una operación de creación de la vista previa a partir del enlace. Esto sustenta la referencia de diseño; no prueba la configuración de la instalación ni sus tiempos efectivos.

- Marcador `popover hover-popover`: byte 2424650 dentro de `app.js`, byte 3188797 del ASAR.
- Marcador `e.prototype.onHoverLink=function`: byte 3527203 dentro de `app.js`, byte 4291350 del ASAR.
- Marcador `e.prototype.onLinkHover=function`: byte 3528376 dentro de `app.js`, byte 4292523 del ASAR.

Decisiones propias de Glosa: apertura sin modificador tras 300 ms, cierre con margen de 180 ms para entrar a la tarjeta, acceso por foco de teclado, Escape, contenido Markdown de la nota nativa y enlace para abrirla. No se copió código del producto.

Verificación: `tests/browser_native_note_links.cjs` usa una base temporal; prueba hover, foco, permanencia al entrar en la tarjeta, posición dentro de la pantalla, Escape, apertura de la nota y regresión de resaltados.

Corrección verificada el 2026-10-17 durante la revisión de DeepSeek: la base de datos del ASAR es `8 + header_size` (segundo entero del encabezado), no `8 + pickle_size` (tercero). La extracción anterior comenzaba cuatro bytes antes. Se corrigieron hash y offsets relativos; los offsets absolutos de los marcadores y las observaciones de diseño se mantienen.
