# Acceso privado con Tailscale

Glosa escucha en `127.0.0.1:8765`. Para acceder desde otro dispositivo, usá
[Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve) dentro de
tu red privada. No habilites Funnel ni expongas el puerto directamente.

Instalá Tailscale en ambos dispositivos e iniciá sesión con la identidad
autorizada. Configurá Serve para reenviar HTTPS al servidor loopback de Glosa.
El archivo local `.local-data/remote-access.json` debe contener el origen HTTPS
exacto y la cuenta que puede acceder:

```json
{
  "origin": "https://tu-equipo.tu-red.ts.net",
  "allowedLogin": "tu-cuenta@example.com"
}
```

Reiniciá Glosa después de configurar el archivo. El servidor comprueba Host,
Origin e identidad insertada por Serve; rechaza Funnel. El archivo y las claves
de dispositivo son privados y no se distribuyen. Consultá `remote_access.py`
para el contrato exacto antes de automatizar una instalación.

La PC debe permanecer encendida y conectada. El celular accede a los mismos
datos de estudio de esa PC; no se sincronizan dos bases independientes.
Los borradores del navegador pueden quedar solo en ese dispositivo.

`scripts/tailscale.sh` y `scripts/enable_remote.py` son ayudas para una instalación
userspace concreta: esperan binarios y socket locales bajo `.local-data/` y una
unidad de usuario `estudio.service`. Esos archivos de sistema no están incluidos
en la distribución. Adaptalos a tu instalación o usá la CLI oficial; ejecutar
`./start.sh` basta para trabajar localmente sin Tailscale.
