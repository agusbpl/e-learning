"""Create a complete study vault atomically, without drafts or import steps."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid

import calendar_store
import rooms


def browse_folders(folder=''):
    """Folder chooser for the web UI: names and paths only, no file contents."""
    if not isinstance(folder, str):
        raise ValueError('Indicá una ruta de carpeta.')
    path = Path(folder).expanduser() if folder.strip() else Path.home()
    if not path.is_absolute():
        raise ValueError('Indicá una ruta absoluta de carpeta.')
    try:
        path = path.resolve(strict=True)
        if not path.is_dir():
            raise ValueError('La ruta no es una carpeta.')
        children = sorted((p for p in path.iterdir() if not p.name.startswith('.')
                           and not p.is_symlink() and p.is_dir()), key=lambda p:p.name.casefold())
    except OSError:
        raise ValueError('No se pudo abrir esa carpeta. Comprobá la ruta y los permisos.') from None
    return {'path': str(path), 'parent': str(path.parent),
            'directories': [{'name': p.name, 'path': str(p)} for p in children[:300]],
            'truncated': len(children)>300}


def inventory(folder, source_files=None):
    if not isinstance(folder, str) or not folder.strip():
        raise ValueError('Indicá la carpeta de fuentes.')
    base = Path(folder).expanduser().resolve(strict=True)
    if not base.is_dir():
        raise ValueError('La carpeta de fuentes no existe.')
    if source_files is not None and (not isinstance(source_files, list) or not source_files
                                     or any(not isinstance(p, str) for p in source_files)):
        raise ValueError('source_files debe ser una lista no vacía de rutas relativas.')
    selected = set(source_files) if source_files is not None else None
    files, skipped = [], []
    # Do not traverse symlink directories, hidden folders, or existing vault internals.
    for current, dirs, names in os.walk(base, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.')
                         and not (Path(current)/d).is_symlink()
                         and d not in ('learning', 'assets', 'Apuntes'))
        for name in sorted(names):
            path = Path(current)/name
            rel = path.relative_to(base).as_posix()
            if selected is not None and rel not in selected:
                continue
            if name.startswith('.') or path.is_symlink() or not path.is_file():
                skipped.append(rel)
                continue
            if path.suffix.lower() not in ('.md', '.txt', '.pdf'):
                skipped.append(rel)
                continue
            size = path.stat().st_size
            if size > 20_000_000 or sum(f['bytes'] for f in files)+size > 200_000_000:
                raise ValueError('Fuentes demasiado grandes: máximo 20 MB por archivo y 200 MB en total.')
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            files.append({'path': rel, 'bytes': size, 'sha256': sha,
                          'documentId': 'doc-'+sha[:24] if path.suffix.lower() == '.pdf' else None})
    if selected is not None and selected != {f['path'] for f in files}:
        raise ValueError('Alguna fuente seleccionada no está disponible dentro de la carpeta o no es Markdown, texto o PDF.')
    if not files:
        raise ValueError('No hay fuentes Markdown, texto o PDF en la carpeta.')
    return {'folder': str(base), 'files': files, 'skipped': skipped,
            'scope': 'Solo esta carpeta; no se siguen enlaces simbólicos. Otros formatos requieren conversión previa.'}


def _import_sources(server, info):
    lib = server.library()
    for item in info['files']:
        path = Path(info['folder'])/item['path']
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('La fuente cambió durante la creación: '+item['path'])
        if path.suffix.lower() == '.pdf':
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(raw))
            if reader.is_encrypted and not reader.decrypt(''):
                raise ValueError('El PDF requiere contraseña: '+item['path'])
            pages = [{'page': n+1, 'text': p.extract_text() or ''} for n, p in enumerate(reader.pages)]
            doc_id = item['documentId']
            directory = lib.data/'documents'
            directory.mkdir(exist_ok=True)
            (directory/(doc_id+'.pdf')).write_bytes(raw)
            (directory/(doc_id+'.json')).write_text(json.dumps({'pages': pages}, ensure_ascii=False))
            doc = {'id': doc_id, 'title': item['path'], 'sha256': item['sha256'], 'pages': len(pages),
                   'storage': 'upload', 'filename': doc_id+'.pdf', 'createdAt': server.now()}
            with lib.connect() as conn:
                conn.execute('INSERT OR IGNORE INTO documents VALUES(?,?)', (doc_id, json.dumps(doc, ensure_ascii=False)))
        else:
            text = raw.decode('utf-8-sig')
            chunks = []
            while text:
                cut = len(text) if len(text) <= 180000 else text.rfind('\n', 0, 180000)+1
                cut = cut or 180000
                chunks.append(text[:cut]); text = text[cut:]
            for index, chunk in enumerate(chunks or ['']):
                note_id = 'source-'+hashlib.sha256(item['path'].encode()).hexdigest()[:24]+'-'+str(index+1)
                title = item['path'][:160]+(f' · {index+1}/{len(chunks)}' if len(chunks)>1 else '')
                lib.save_note({'id': note_id, 'title': title, 'folder': 'Fuentes', 'content': chunk,
                               'shared': True, 'documentId': None, 'page': None, 'anchors': []})


def create(server, folder, title, course, rationale, validate, calendar_events=None,
           study_plan=None, source_files=None):
    if not isinstance(title, str) or not title.strip() or len(title)>200:
        raise ValueError('Indicá un título de pliego de hasta 200 caracteres.')
    if not isinstance(rationale, str) or not rationale.strip() or len(rationale)>20000:
        raise ValueError('Explicá fuentes, cobertura, revisión semántica y decisiones pedagógicas.')
    if calendar_events is not None and not isinstance(calendar_events, list):
        raise ValueError('calendar_events debe ser una lista.')
    if study_plan is not None and (not isinstance(study_plan, dict) or
            set(study_plan)-{'examDate', 'weekdayMinutes', 'weekendMinutes', 'dailyOverrides'}):
        raise ValueError('study_plan admite examDate, weekdayMinutes, weekendMinutes y dailyOverrides.')
    info = inventory(folder, source_files)
    # Atomic publication into the configured Margen. Failure leaves no empty pliego.
    with rooms.LOCK:
        margen = Path(rooms.margen(server.DATA)['path'])
        if not margen.is_dir():
            raise ValueError('La carpeta del Margen no está disponible.')
        with tempfile.TemporaryDirectory(prefix='.author-', dir=margen) as temp:
            stage = Path(temp)/'pliego'
            stage.mkdir(); (stage/'assets').mkdir(); (stage/'learning').mkdir()
            room_id = 'pliego-'+uuid.uuid4().hex
            metadata = {'format': 'glosa-pliego', 'version': 1, 'id': room_id, 'title': title.strip()}
            (stage/'pliego.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
            token = server.ACTIVE_WORKSPACE.set({'id': room_id, 'root': stage/'assets', 'data': stage/'learning'})
            try:
                server.init_db()
                _import_sources(server, info)
                result = validate(course)
                if not result.get('valid'):
                    raise ValueError('Corregí la calidad del curso: '+json.dumps(result, ensure_ascii=False))
                # Reject local PDF URLs that do not travel with this vault.
                for source in course.get('sources', []):
                    url = source['url']
                    if url.startswith('/sources/'):
                        raise ValueError('Usá /documents/ID para PDFs de la carpeta; no referencias /sources/ ajenas al pliego.')
                state = server.snapshot()
                state['courses'] = [course]
                state['settings'].update(study_plan or {})
                state['calendarEvents'] = [calendar_store.validate({**ev, 'courseId': course['id'],
                    'id': ev.get('id') or str(uuid.uuid4()), 'revision': 1}) for ev in (calendar_events or [])]
                if len({ev['id'] for ev in state['calendarEvents']}) != len(state['calendarEvents']):
                    raise ValueError('IDs de calendario duplicados.')
                server.restore_snapshot(state)
                (stage/'autoria.json').write_text(json.dumps({'rationale': rationale, 'sources': info,
                    'courseId': course['id'], 'courseVersion': course['version'], 'createdAt': server.now(),
                    'validation': result}, ensure_ascii=False, indent=2)+'\n')
                restored = server.snapshot()
                assert len(restored['courses']) == 1 and not restored['events']
            finally:
                server.ACTIVE_WORKSPACE.reset(token)
            target = rooms._unique_folder(margen, rooms.safe_folder_name(title))
            stage.rename(target)
    return {'id': room_id, 'title': title.strip(), 'path': str(target), 'status': 'ready',
            'courseId': course['id'], 'lessons': len(course['lessons']),
            'sources': len(info['files']), 'warnings': result.get('warnings', []),
            'message': 'Pliego completo creado en el Margen configurado. Abrí GLOSA → Margen y elegilo. Sin importación ni ZIP.'}
