# Encargo para retomar las mejoras de Glosa

Copiar este mensaje en una conversación nueva con el agente que vaya a trabajar en Glosa:

---

Trabajá en `<HOME>/Documents/glosa`. Quiero retomar las posibles mejoras de Glosa investigadas el 17/10/2026. Su propósito principal es estudiar para parciales.

Primero leé `AGENTS.md` y estos documentos:

- `docs/investigaciones/2026-10-17-profunda/README.md`
- `docs/investigaciones/2026-10-17-profunda/INVENTARIO.md`
- `docs/investigaciones/2026-10-17-profunda/inventario.json`

Presentame las opciones agrupadas por necesidad, con sus IDs `G01`–`G58`, y señalá cuáles ya existen parcialmente y qué cambiaría para mí. No vuelvas a proponer como nuevas funciones que Glosa ya tiene. Esta primera lectura y presentación no autoriza implementar ninguna.

Después voy a elegir por ID o por nombre y agregar preferencias, por ejemplo: «Quiero G05 y G19, pero el repaso debe durar como máximo veinte minutos y quiero poder elegir las unidades». Mis ajustes tienen prioridad sobre las adaptaciones sugeridas en el inventario.

Cuando elija:

1. Convertí mi selección y mis ajustes en un alcance concreto. Si la elección es clara, continuá con el trabajo autorizado sin pedirme una confirmación redundante. Preguntá solo lo que falte y afecte materialmente el resultado; avanzá con lo independiente mientras tanto.
2. Volvé a inspeccionar el código actual: el inventario es una referencia fechada, no garantía de que el estado siga igual. Conservá los IDs de investigación aunque cambie la implementación.
3. Identificá dependencias y conflictos entre opciones. Resolvé detalles internos necesarios dentro del alcance; no sumes otras funciones de producto porque estén en la lista. Si una dependencia requiere ampliar materialmente lo elegido, explicámelo antes de incluirla.
4. Consultá `EVIDENCIA.md` y los informes de referencia cuando sean relevantes. Distinguí resultados REA, lectura estática, límites y propuestas propias. No hace falta repetir la investigación de Obsidian/Okular/KOReader si el trabajo se resuelve con el código de Glosa; usá la skill REA si necesitás nuevas afirmaciones sobre sus artefactos o comportamiento.
5. Adaptá los criterios de aceptación a mis ajustes y verificá el resultado con pruebas apropiadas y bases temporales. La validación mecánica no sustituye revisión semántica ni demuestra aprendizaje.
6. Conservá IDs, fuentes, historial y borradores. No escribas respuestas simuladas en bases reales. No habilites Funnel. Los términos deben seguir enlazados dentro de las lecciones, con notas nativas; no reintroduzcas un glosario separado obligatorio.
7. Aplicá `docs/evaluacion-rigurosa.md` cuando corresponda: tiempo, lectura, autoevaluación y ayuda recibida no acreditan dominio; después de ayuda se requiere una aplicación independiente diferente.
8. Reportá qué IDs se implementaron, mis ajustes incorporados, pruebas ejecutadas y limitaciones. Actualizá un registro fechado de implementación sin reescribir la investigación histórica como si hubiese descrito el estado nuevo.

Los informes y el inventario están conservados en el repositorio; las capturas crudas de evidencia permanecen en el respaldo local, como explica `docs/investigaciones/README.md`. Hay scripts con rutas absolutas y referencias adicionales a `/tmp`; si esos temporales ya no existen, no asumas que están disponibles ni que eso invalida los documentos conservados. Revisá qué necesita reproducirse para el cambio elegido.

No implementes las 58 opciones: primero presentámelas y esperá mi selección.

---

## Ejemplos de selección del estudiante

- «G05: al cerrar una preview quiero volver al mismo párrafo; no quiero otra pestaña».
- «G19 y G24, pero con repaso de veinte minutos y unidades elegidas por mí».
- «G01 primero, usando solo búsqueda local y con salto a la coincidencia».

Son ejemplos de preferencias, no decisiones ya tomadas por el estudiante.
