# Seguridad

Si encontrás una vulnerabilidad, evitá publicarla primero en un issue o PR. No incluyas secretos, datos personales, PDFs ni respaldos en el reporte. Usá [Report a vulnerability](https://github.com/agusbpl/glosa/security/advisories/new) en la pestaña Security del repositorio: los reportes privados están habilitados. Si GitHub no muestra esa opción, solicitá a la persona mantenedora un canal privado sin publicar detalles técnicos de la vulnerabilidad.

Indicá versión o commit, pasos mínimos con datos ficticios e impacto observado. Se agradece divulgación coordinada. Antes de definir una política de releases no se prometen plazos de respuesta ni soporte para versiones específicas.

El despliegue previsto es local para una persona en loopback, con acceso remoto solo por Tailscale Serve privado. No expongas Glosa directamente a Internet, habilites Funnel ni lo operes como SaaS multiusuario público. Ver [privacidad](docs/privacidad.md).
