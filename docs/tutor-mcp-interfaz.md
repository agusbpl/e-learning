# Elegir cómo conversar: API o canal MCP externo

La conversación de estudio puede seguir dos caminos, y los elegís desde **Ajustes
→ Canal del tutor**:

- **API directa (clave del proveedor).** Es el tutor integrado de siempre: Glosa
  llama al proveedor configurado con tu clave y responde en el acto.
- **MCP externo (sin clave).** Glosa no llama a ningún proveedor ni usa tu clave:
  guarda tu consulta como **pendiente** para que la responda un cliente externo
  con el MCP de tutor (`tutor_mcp.py`), con **tu** modelo y **tu** cuenta.

La elección se guarda en este navegador (como el tema) y sobrevive al recargar.
No promete una cuenta externa gratuita universal: el costo y el modelo son los de
tu propio programa externo.

## Conectar el cliente externo

El servidor es stdio y se lanza con el mismo runtime local:

```text
/ruta/absoluta/glosa/start-tutor-mcp.sh
```

Un cliente con configuración `mcpServers` puede usar:

```json
{
  "mcpServers": {
    "estudio-tutor": {
      "command": "/ruta/absoluta/glosa/start-tutor-mcp.sh"
    }
  }
}
```

Necesita el mismo directorio de datos (`LEARNING_DATA_DIR`) que la plataforma y
**no** requiere `OPENROUTER_API_KEY`. Herramientas, pliegos y flujo completo
están en [mcp-tutor.md](mcp-tutor.md).

## Qué pasa al preguntar con el canal MCP

1. Elegís un fragmento y **Consultar al tutor** (o escribís en el panel). La
   consulta se guarda como pendiente con un ID determinista
   (`<request_id>-pregunta`); no se crea ninguna respuesta automática.
2. El panel muestra el aviso **«Pendiente para el canal MCP externo»** y el
   estado **Canal MCP externo**.
3. Tu agente externo pide el contexto (`tutor_brief`) y registra su respuesta
   (`register_tutor_exchange`) con su modelo.
4. Volvés a la interfaz y usás **⟳ Recargar conversación** (panel) o **Actualizar
   conversación** (diálogo de apunte). No se recarga la página: se reconsulta el
   estado y se conservan tus borradores.

Cuando la respuesta ya está registrada, aparece con la procedencia **Agente
externo · `<modelo>`**, para no atribuirle al proveedor configurado lo que dijo
otro modelo. La respuesta es una **ayuda conversada**: no acredita dominio
independiente.

## Apuntes y PDF

El canal elegido también vale para **Notas**: al preguntar desde un apunte o una
página de PDF, la consulta queda pendiente en el registro del apunte con su
contexto (nota, página y fuente). Responderla desde el MCP usa las mismas reglas
de contexto y privacidad que la API. Mientras esa respuesta no llegue, la
consulta se conserva pendiente y podés actualizarla sin perder el borrador.

## Resaltados retirados

Un resaltado que quitaste (**Quitar resaltado**) deja de ofrecerse al contexto
automático del tutor, aunque su historial completo sigue en tu registro y en las
exportaciones. Volver a resaltar el mismo fragmento crea un resaltado nuevo.
