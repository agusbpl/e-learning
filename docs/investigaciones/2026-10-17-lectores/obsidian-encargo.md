Investigá con DeepSeek de OpenCode qué features del Obsidian instalado convendría agregar o rearmar en Glosa. Tu misión es investigación y propuestas, NO implementar cambios.

Usá obligatoriamente la skill <HOME>/.agents/skills/reverse-engineer-anything/SKILL.md: leela y seguí su flujo. Obsidian ya está identificado: /usr/lib/obsidian/obsidian.asar (app.js/app.css), /usr/lib/obsidian/app.asar. REA CLI está instalada en <HOME>/.local/bin/rea versión 6.4.0. Usá herramientas REA disponibles o esa CLI para obtener evidencia real; no basta leer la skill o sugerir features de memoria. No es necesario activar un MCP pendiente si la CLI sirve. No hacer setup global ni modificar configuraciones.

Propósito: Glosa es ante todo para preparar parciales próximos. Importa comprender relaciones, practicar recuperación y aplicación, detectar errores, planificar repasos según fecha/temario/tiempo, consultar fuentes sin perder el hilo. No convertirla en un clon general de Obsidian ni proponer organización por organización.

Leé archivos de código y docs de <HOME>/Documents/glosa para conocer lo existente (README.md, docs/herramientas-estudio.md, docs/evaluacion-rigurosa.md, docs/modos-tutor.md, docs/formato-cursos.md, web/study-tools.js, web/app.js, web/notes.js, web/plan.js, web/keyboard.js y otros relevantes). Fuente completa de Glosa: usar herramientas normales, NO REA para analizar este repo. Ya existen cursos/actividades/simulacros, notas nativas Markdown, enlaces y preview hover de términos en lecciones, referencias cruzadas/menciones/fichas/metadata y registro de errores en Notas, planificación de parciales y tutor con modos. Separá existente, mejora de existente y nuevo; verificá con archivos/líneas.

Privacidad y alcance: solo código/documentación del repositorio y artefactos instalados de Obsidian. NO leer ~/Margen, <HOME>/Margen, fuentes de materias, .local-data, bases reales, credenciales, notas personales o bóvedas de Obsidian. No arrancar Obsidian ni modificar datos reales. No cambios al repositorio. Escribir solo /tmp/glosa-obsidian-research/. No delegar a más modelos ni cambiar de modelo/proveedor. Sin consultas pagas. No navegación web necesaria. Si analizás código empaquetado, describí comportamiento y evidencia; no copiar implementación propietaria.

Ya hubo un análisis REA general de obsidian.asar que agotó 30 segundos; esto no prueba ausencia de features. Evitá repetir igual. Usá resumen y alcance reducido, extracción de miembros/foco local si hace falta; preservá hash del original y offsets, referencias de evidencia y límites. La skill explica cómo consultar evidencia parcial y reducir análisis. Tu ejecución debe incluir al menos una operación real de REA y las evidencias focalizadas que permitan sostener las propuestas. Diferenciá estático, observado en runtime e inferido. No afirmar ejecución observada si no ocurrió.

Entregá /tmp/glosa-obsidian-research/informe-deepseek.md en español con:
1. Modelo usado y metodología con comandos realmente ejecutados, hashes/evidence IDs y límites.
2. 6–10 propuestas concretas priorizadas para parciales, para cada una: feature Obsidian comprobada y evidencia localizable; estado real de Glosa con referencias; interacción concreta del estudiante; beneficio esperado como hipótesis (no promesa de aprendizaje); adaptación mínima; dificultad/riesgo y criterio de aceptación verificable. No duplicar lo que ya hay.
3. Tres prioridades para empezar y por qué; 3 cosas de Obsidian que NO conviene trasladar para este propósito.
4. Qué no pudo verificarse. Lista de artefactos de evidencia bajo /tmp/glosa-obsidian-research/.

Aplicá la regla evaluación rigurosa: autoevaluación, lectura, marcar completado y ayuda recibida no acreditan dominio; la evidencia independiente se comprueba después de la ayuda. No usar LLM para azar. No inventar estudios, referencias o resultados.

Al terminar, devolvé resumen breve, ruta al informe y si hubo algún bloqueo. Persistí hasta completar la investigación acotada; no modificar Glosa.
