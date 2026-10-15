# Glosa

Glosa es una aplicación personal de estudio con cursos referenciados, apuntes junto a PDFs, actividades, historial y un tutor opcional conectado a un proveedor de modelos. Guarda los datos de estudio localmente y se sirve en loopback para una persona.

## Empezar

```bash
git clone https://github.com/agusbpl/glosa.git
cd glosa
./start.sh
```

Abrí <http://127.0.0.1:8765>. Necesitás Python 3.11 o posterior. La distribución pública se prepara sin claves, respuestas, apuntes ni PDFs personales mediante la [lista de release](docs/release.md). Podés crear un pliego vacío, importar un curso propio o usar Primer trazo para conocer la interfaz.

El arranque y las pruebas se verificaron en Linux con Bash y Chromium. Otros sistemas y navegadores todavía requieren verificación.

La extracción de PDFs y la autoría MCP requieren dependencias adicionales:

```bash
python3 -m venv .venv-author
.venv-author/bin/python -m pip install -r requirements-author.txt
```

Para pruebas y estructura del proyecto, consultá [desarrollo](docs/desarrollo.md). El [acceso remoto](docs/acceso-remoto.md) usa Tailscale Serve privado. Glosa no está diseñada como servicio público multiusuario: no expongas el servidor directamente a Internet ni habilites Tailscale Funnel.

## Uso y datos

En **Margen** se organizan los pliegos con cursos, lectura, notas y conversación. Cada pliego puede exportarse como ZIP con PDFs e historial. Revisá el contenido antes de compartirlo; los borradores aún presentes solo en el navegador pueden quedar fuera de la exportación.

El tutor es opcional. Al usarlo, el contexto elegido se envía al proveedor configurado. Las credenciales permanecen en la instalación local de la PC, fuera de los respaldos de pliegos. Las condiciones y costos dependen del proveedor. Leé [privacidad](docs/privacidad.md).

Los cursos y las evaluaciones requieren revisión humana de fuentes y rúbricas. La [regla de evaluación rigurosa](docs/evaluacion-rigurosa.md) describe los criterios del proyecto; las comprobaciones automáticas no acreditan calidad pedagógica por sí solas.

## Participar

El código de Glosa se distribuye bajo [Apache License 2.0](LICENSE). Las contribuciones se reciben bajo la misma licencia; consultá [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) y [SUPPORT.md](SUPPORT.md). Las bibliotecas vendorizadas conservan sus licencias, indicadas en [NOTICE](NOTICE). La distribución usa un árbol y una historia filtrados según la [revisión de release](docs/release.md); los materiales de terceros necesitan permisos independientes.
