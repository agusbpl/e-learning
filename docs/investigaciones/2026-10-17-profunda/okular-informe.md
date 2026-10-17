# Okular: análisis funcional acotado con REA + Ghidra

Fecha: 2026-10-17. Coordinador. Target original `/usr/lib/libOkular6Core.so.4.0.0`, SHA-256 `e011663feccf9977bb33af31cde27540c78a3ac19eab3cbcbad36a9c5944ad08`.

## Qué se logró ahora

Se encontró Ghidra 12.1.2 en `/opt/ghidra` y Java 21. Se seleccionó el proveedor Ghidra mediante entorno local, sin modificar configuración global. El análisis completo de `okularpart.so` y del núcleo se interrumpió durante autoanálisis (salidas conservadas en `overview.json`, `core-functions.json` y `retry/core-functions.json`, exit 143); no se diagnosticó definitivamente quién provocó esas terminaciones. Reducir el máximo de heap y ampliar la ventana no bastó para completar el binario entero.

En lugar de repetir el mismo análisis se construyó un **ELF derivado de 14.120 bytes** con nueve funciones originales copiadas byte a byte, sin recompilar su implementación. Se preservaron sus direcciones virtuales. `fragments/provenance.json` conserva hash original, hash derivado, símbolo, offset, tamaño y hash de cada fragmento. `extract_native.py` verifica que cada secuencia es idéntica a los bytes del original. El contenedor y los nombres `REA_*` son auxiliares, no parte del producto original.

REA abrió ese ELF con Ghidra, completó su autoanálisis y generó **seis dossiers `analyze_function`** con pseudocódigo, assembly, bloques básicos, referencias y flujo de valores. Los resultados completos y el bundle se exportaron antes de cerrar la sesión. No se ejecutó Okular ni el ELF derivado.

## Evidencia funcional obtenida por REA

| Función original | Dirección virtual original | Evidence ID del dossier | Observación acotada e implicación para Glosa |
|---|---|---|---|
| `BookmarkManager::nextBookmark` | `0x78530` | `ev_1e19c5d71b92a817e147a270fa3676184e1415878db6992a39f02cd46820997c` | En el cuerpo recuperado hay ordenación/recorrido de elementos y un recorrido hacia adelante que elige mediante comparación con la posición actual. Referencia para avanzar por marcas con destino preciso. Los tipos/llamadas Qt externos no se resolvieron. |
| `BookmarkManager::previousBookmark` | `0x78af0` | `ev_b6692368f431fa2cce049decd3bb2e1ae9621a40e6bfbfb9a4b5cf44eef6c7b5` | Recorrido inverso con comparación de la posición. Fundamenta que «anterior» debe conservar orden de ubicación, no solo orden de creación. No demuestra comportamiento circular ni la interfaz efectiva. |
| `DocumentViewport::operator<` | `0xa7ca0` | `ev_ef7fa65fedd087ab3a15c2ea68d2fae9869494c1aa2a83836c60f55cae485406` | Compara un entero inicial; en igualdad y con los indicadores habilitados compara dos doubles, primero el segundo y después el primero. La cabecera distribuida identifica estos campos como página, `rePos.enabled`, `normalizedY`, `normalizedX`. Así se corrobora una ubicación dentro de la página, más precisa que guardar solo número. |
| `DocumentViewport::toString` | `0xa7500` | `ev_0b38ef8390a4946813fa6a293fb64f01b70e0618d1336b576e389a6544a1b079` | Recupera un cuerpo con bifurcaciones según campos y conversiones/ensamblado de valores. La firma distribuida confirma serialización a QString. Los literales y funciones Qt externos no permiten reconstruir aquí el formato textual completo. Referencia para persistir una ubicación de lectura estructurada. |
| `Document::continueSearch(int)` | `0x9d860` | `ev_95c488b21bf45b244764ba557a47c4c509e621328616109ef534dc27c76e84ef` | Busca por el entero de entrada en una estructura arbórea, revisa flags y despacha por rutas distintas según encuentre estado. Con la firma exportada se interpreta como continuación de una búsqueda por ID. Útil para no mezclar varias búsquedas/documentos en Glosa. La llamada indirecta final sigue sin resolver. |
| `Document::setViewportPage` | `0x9b1a0` | `ev_00b402497a2c49756ebca9f70d1e34dbd47734434b7f99641c54dcc7d690820c` | Hay comprobaciones del número recibido contra cero y un límite leído del documento, seguidas de construcción/despacho de una posición. Es evidencia de validación en el salto; no se deriva un contrato exacto de límites ni un supuesto error de una desigualdad decompilada. |

Inventario de funciones del fragmento: `ev_dc655c41b05c0c565bae3a77b65557db610360f87b2cdcb24a2e469862015fcc`.

## Límites de esta reconstrucción

- El artefacto analizado es **derivado**, no el ELF completo de Okular. Preservar bytes y direcciones no conserva automáticamente imports, relocaciones, datos globales, strings ni todo el contexto de llamadas.
- Los saltos/llamadas hacia código no incluido quedan sin resolver. El pseudocódigo incluye advertencias de flujo truncado, datos globales superpuestos y saltos indirectos; se conservan en los dossiers. No se trasladan nombres de campos de la cabecera al pseudocódigo como si Ghidra los hubiera recuperado.
- La correspondencia con los métodos originales se obtiene de símbolos exportados del binario original, sus direcciones y tamaños; esa identificación es evidencia de herramientas ordinarias complementaria a REA.
- La validación byte a byte acredita procedencia del fragmento, no equivalencia del comportamiento global de la aplicación. No se ejecutó ni se pretende ejecutar el contenedor derivado.
- El intento completo no se presenta como exitoso. El resultado funcional útil es el conjunto de seis funciones acotadas, con estos límites.

## Qué cambiaría en Glosa a partir de esto

1. Ubicaciones estables de lectura: documento+versión/página+posición relativa dentro de la página, bloque de lección y caret del apunte. Regresar debe validar identidad y conservar borrador.
2. Anterior/siguiente por marcador con un orden explícito de ubicación, separado del historial por recencia y de los errores por prioridad de repaso.
3. Estado independiente de búsqueda por documento/consulta; retomar un resultado no debe mezclar consultas previas.
4. Salto de página visible con validación y distinción entre página PDF y etiqueta impresa.
5. Enlazar resultados, citas y conceptos a esas ubicaciones, y recuperar el punto de origen al volver.

Estas son adaptaciones de diseño, no funciones recuperadas de Glosa ni pruebas de mejora de aprendizaje. Las demás ideas de Okular (índice, miniaturas, anotaciones, modos) conservan la evidencia estática de la primera pasada; no se rebautizan como hallazgos de estos dossiers.

## Reproducibilidad

`extract_native.py` crea el corpus reducido y comprueba sus bytes; `fragment_probe.py` abre un servidor MCP REA propio con `GHIDRA_INSTALL_DIR=/opt/ghidra`, `GHIDRA_HEADLESS_MAXMEM=512M`, `REA_GHIDRA_STARTUP_TIMEOUT_MS=600000`, ejecuta las búsquedas y los seis análisis, exporta el bundle y cierra. `fragments/*.c.txt` son vistas legibles del pseudocódigo conservado en las evidencias JSON, no código fuente original.
