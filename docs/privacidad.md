# Privacidad y despliegue

Glosa guarda localmente cursos importados, respuestas, notas, comentarios, conversaciones, historial y documentos. Un ZIP de pliego puede contener PDFs e historial completo; tratá cada respaldo como privado. Los registros sin procesar del tutor pueden incluir contenido sensible y no deben publicarse como ejemplos, adjuntos de issues ni artefactos de CI.

Las credenciales del proveedor se almacenan en la PC que ejecuta Glosa, fuera del respaldo del pliego. Al consultar al tutor, la pregunta y el contexto elegido se envían al proveedor seleccionado. Comprobá el contenido y las condiciones del proveedor antes de enviar apuntes o fuentes con restricciones. Una exportación para un agente externo requiere la misma revisión.

Los videos incrustados y las imágenes remotas pueden cargar contenido desde terceros, que reciben las peticiones del navegador. Revisá los recursos de un curso y sus políticas antes de abrirlos. Las pruebas automatizadas usan recursos interceptados o sintéticos cuando necesitan comprobar esas integraciones.

El despliegue previsto es en `127.0.0.1` y, si se necesita acceso remoto, mediante Tailscale Serve privado con identidad autorizada. No expongas Glosa como SaaS público multiusuario ni habilites Tailscale Funnel. Protegé también el dispositivo, la cuenta Tailscale y las copias de respaldo.

Los PDFs y otros materiales de cátedra o terceros conservan sus propios derechos. La licencia del código no concede permiso para redistribuirlos. Eliminá datos personales, secretos y fuentes sin autorización antes de compartir una reproducción o abrir un issue.
