# Historial de cambios

## 0.1.0 · candidata sin publicar

Preparada el 2026-10-15. La fecha de publicación se fija al crear la release.

- Preparación de la primera release abierta: documentación de instalación, privacidad, contribución, seguridad y licencia Apache-2.0.
- Notas con Markdown durante la escritura, Foco, Vim y selección visual; ayuda de la tecla líder y modo PDF con celdas por página.
- Gestión de apuntes, resaltados y consultas al tutor conservando revisiones e historial.
- Distribución pública mediante lista explícita y manifiesto SHA-256, sin datos locales ni historia Git privada.
- Pruebas reproducibles con material sintético y CI para Python y navegador.
- Correcciones de redirecciones autenticadas, validación HTTP/importaciones, activación nativa con Espacio y conservación del lector al cambiar metadatos de notas.

- Tutorial `1.0.2`: explica la persistencia local de las claves, conserva los IDs y permite completar la guía sin reproducir el video.
- Las pruebas comprueban que el PDF conserva su última página al reabrir y que sus consultas no se mezclan con las de otro apunte.

- Se corrigió la oscilación del PDF al abrirlo con barras de desplazamiento clásicas: el lector reserva su espacio antes de ajustar la página al ancho. La prueba nueva falla con el código anterior y comprueba también la resolución eDP de 1366×768. No se integró el parche experimental anterior.

Resultados y límites en [la auditoría](docs/auditoria-release.md). La publicación queda pendiente de completar [la verificación de release](docs/release.md).

