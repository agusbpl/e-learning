"""Reúne la presentación y sus scripts locales en un HTML autónomo."""
from pathlib import Path
import base64

root = Path(__file__).resolve().parent
html = (root / "mejoras.html").read_text()
for name in ("vendor/gsap.min.js", "lectura-escena.js", "mejoras.js", "escenografia.js", "apertura.js"):
    source = (root / name).read_text().replace("</script", "<\\/script")
    html = html.replace(f'<script src="{name}"></script>', f'<script>\n{source}\n</script>')
html = html.replace('<link rel="stylesheet" href="escenografia.css">', '<style>' + (root / 'escenografia.css').read_text() + '</style>')
image = base64.b64encode((root / 'ilustraciones/glosa-tutora.png').read_bytes()).decode()
html = html.replace('ilustraciones/glosa-tutora.png', 'data:image/png;base64,' + image)
html = html.replace('<link rel="stylesheet" href="apertura.css">', '<style>' + (root / 'apertura.css').read_text() + '</style>')
for name, mime in [('video/glosa-apertura-sin-audio.mp4', 'video/mp4'), ('video/glosa-apertura-poster.jpg', 'image/jpeg')]:
    encoded = base64.b64encode((root / name).read_bytes()).decode()
    html = html.replace(name, f'data:{mime};base64,{encoded}')
(root / "glosa-interactiva.html").write_text(html)
