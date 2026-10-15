# Desarrollo

El servidor requiere Python 3.11 o posterior y usa SQLite para el estado local. La interfaz está en `web/`. La distribución pública incluye `courses/tutorial.json`; los cursos personales y PDFs quedan fuera. La autoría MCP y la extracción PDF usan `requirements-author.txt`.

Ejecutá `./start.sh` y abrí <http://127.0.0.1:8765>. Si el puerto está ocupado, detené la instancia anterior. El despliegue previsto es loopback para una sola persona, o Tailscale Serve privado. No habilites Funnel ni lo conviertas en un servicio público multiusuario.

Trabajá con bases temporales; no crees respuestas ficticias ni reinicies el historial real. `.local-data/`, las exportaciones y los PDFs personales no son artefactos de release.

Comandos de verificación disponibles (revisá primero sus requisitos y ubicación de datos):

```bash
python3 -m unittest discover -s tests -v
.venv-author/bin/python scripts/check_author_mcp.py
npm ci
npx playwright install chromium
npm run test:browser
```

El runner también acepta nombres concretos, por ejemplo
`npm run test:browser -- browser_vim.cjs browser_notes_workspace.cjs`.
Para usar un Chromium ya instalado, indicá `PLAYWRIGHT_CHROMIUM_EXECUTABLE`.
`GLOSA_TEST_AUTHOR_VENV` permite usar un entorno de autoría externo en las
fixtures temporales; normalmente se usa `.venv-author` de la instalación.

Las pruebas de navegador requieren Node.js 20 o posterior, Playwright y Chromium. El runner ejecuta los recorridos `tests/browser_*.cjs` con fixtures sintéticas y datos temporales. CI comprueba Python 3.11 y 3.12; el editor se reconstruye por separado siguiendo [sus instrucciones](../web/editor/README.md). Las pruebas del software no sustituyen revisión semántica de cursos o respuestas de un modelo real. Aplicá [evaluación rigurosa](evaluacion-rigurosa.md) al cambiar esas partes. Para la publicación, seguí [release.md](release.md). Al modificar cursos, conservá IDs y trazabilidad; consultá [formato de cursos](formato-cursos.md).
