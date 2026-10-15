"""Build a disposable software fixture; never copy a student's course or sources."""
import hashlib
import json
import os
from pathlib import Path
import shutil


REPO = Path(__file__).resolve().parents[2]


def fixture_pdf(pages=2):
    def stream(number):
        return f'BT /F1 18 Tf 40 700 Td (PDF temporal pagina {number}) Tj ET'
    objects = [
        '<< /Type /Catalog /Pages 2 0 R >>',
        f'<< /Type /Pages /Kids [{" ".join(f"{3+n} 0 R" for n in range(pages))}] /Count {pages} >>',
        *[f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {3+pages*2} 0 R >> >> /Contents {3+pages+n} 0 R >>' for n in range(pages)],
        *[f'<< /Length {len(stream(n))} >>\nstream\n{stream(n)}\nendstream' for n in range(1, pages+1)],
        '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    ]
    pdf = b'%PDF-1.4\n'
    offsets = [0]
    for number, body in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf += f'{number} 0 obj\n{body}\nendobj\n'.encode()
    xref = len(pdf)
    pdf += f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode()
    pdf += ''.join(f'{offset:010d} 00000 n \n' for offset in offsets[1:]).encode()
    pdf += f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()
    return pdf


def fixture_course(pages=2):
    tutorial = json.loads((REPO / 'courses/tutorial.json').read_text())
    source = fixture_pdf(pages)
    lesson = tutorial['lessons'][0]
    lesson['blocks'][0]['references'] = [{'sourceId': 'fixture-pdf', 'page': 1}]
    lesson['exercises'].insert(0, {
        'id': 'fixture-choice', 'type': 'choice',
        'question': '¿Cuál de estas acciones guarda una anotación?',
        'options': ['Guardar una nota', 'Cerrar la vista', 'Cambiar de modo'],
        'correctIndex': 0, 'rubric': ['Identificar la acción de guardar'],
    })
    tutorial.update(id='fixture-software', version='1.0.0', title='Fixture temporal de software',
                    sources=[{'id': 'fixture-pdf', 'title': 'PDF temporal',
                              'url': '/sources/fixture.pdf', 'pages': pages,
                              'sha256': hashlib.sha256(source).hexdigest()}])
    return tutorial


def build(destination, browser=False):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'courses').mkdir(exist_ok=True)
    (destination / 'sources').mkdir(exist_ok=True)
    (destination / '.md_cache').mkdir(exist_ok=True)
    (destination / 'output/qa').mkdir(parents=True, exist_ok=True)
    for source in REPO.glob('*.py'):
        shutil.copy2(source, destination / source.name)
    (destination / 'scripts').mkdir(exist_ok=True)
    for script in ('extract_document.py', 'room_backup.py', 'validate_course.py'):
        shutil.copy2(REPO / 'scripts' / script, destination / 'scripts' / script)
    (destination / 'web').symlink_to(REPO / 'web', target_is_directory=True)
    (destination / 'docs').symlink_to(REPO / 'docs', target_is_directory=True)
    if browser:
        shutil.copytree(REPO / 'tests', destination / 'tests', ignore=shutil.ignore_patterns('__pycache__'))
        (destination / 'node_modules').symlink_to(REPO / 'node_modules', target_is_directory=True)
    author_venv = Path(os.environ.get('GLOSA_TEST_AUTHOR_VENV', REPO / '.venv-author'))
    if author_venv.exists():
        (destination / '.venv-author').symlink_to(author_venv, target_is_directory=True)
    pages = 30 if browser else 2
    (destination / 'courses/default.json').write_text(json.dumps(fixture_course(pages), ensure_ascii=False))
    shutil.copy2(REPO / 'courses/tutorial.json', destination / 'courses/tutorial.json')
    (destination / 'sources/fixture.pdf').write_bytes(fixture_pdf(pages))
    (destination / '.md_cache/fixture-pdf.json').write_text(json.dumps({'pages': [
        {'page': page, 'text': f'PDF temporal pagina {page}'} for page in range(1, pages+1)
    ]}))
    if browser:
        # The media route is exercised using synthetic bytes, never a personal video.
        web = destination / 'web'
        web.unlink()
        shutil.copytree(REPO / 'web', web, ignore=shutil.ignore_patterns('media', 'node_modules', '__pycache__'))
        (web / 'media').mkdir()
        (web / 'media/fixture-demo.mp4').write_bytes(b'GLOSA-SYNTHETIC-MEDIA-' * 50)
    return destination


if __name__ == '__main__':
    import sys
    build(sys.argv[1], browser='--browser' in sys.argv[2:])
