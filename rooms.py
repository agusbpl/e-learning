"""Separate local study rooms; the registry belongs to the installation, not Git."""
import base64
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import threading
import uuid
import zipfile

LOCK = threading.RLock()
TUTORIAL_ID = 'primer-trazo'


def margen(data):
    config = Path(data)/'margen.json'
    saved = json.loads(config.read_text()).get('path') if config.exists() else None
    configured = os.environ.get('GLOSA_MARGEN_DIR')
    path = Path(configured or saved or Path(data)/'margen').expanduser().resolve()
    if not configured and not saved:
        path.mkdir(parents=True, exist_ok=True)
    return {'path': str(path), 'source': 'environment' if configured else 'settings' if saved else 'default'}


def set_margen(data, folder):
    if os.environ.get('GLOSA_MARGEN_DIR'):
        raise ValueError('El Margen está definido por GLOSA_MARGEN_DIR; cambiá esa variable para elegir otro.')
    if not isinstance(folder, str) or not folder.strip() or not Path(folder).expanduser().is_absolute():
        raise ValueError('Indicá la ruta absoluta de una carpeta existente.')
    path = Path(folder).expanduser().resolve()
    if not path.is_dir():
        raise ValueError('La carpeta del Margen no existe.')
    with LOCK:
        pending = Path(data)/'margen.json.tmp'
        pending.write_text(json.dumps({'path': str(path)}, ensure_ascii=False)+'\n')
        pending.replace(Path(data)/'margen.json')
    return margen(data)


def inventory(data, root):
    """Discover live folders without copying them or modifying their databases."""
    location = margen(data)
    entries, backups, warnings = [], [], []
    directory = Path(location['path'])
    if not directory.is_dir():
        warnings.append('La carpeta del Margen no está disponible: '+str(directory))
    else:
        for folder in sorted(directory.iterdir()):
            if folder.is_symlink() or not folder.is_dir() or folder.name.startswith('.'):
                continue
            metadata = folder/'pliego.json'
            try:
                if metadata.is_file():
                    if metadata.is_symlink() or metadata.stat().st_size > 16_000:
                        raise ValueError('Metadatos inválidos.')
                    item = json.loads(metadata.read_text())
                    if item.get('format') != 'glosa-pliego' or item.get('version') != 1 or not isinstance(item.get('id'), str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', item['id']) or item['id'] in ('local', TUTORIAL_ID):
                        raise ValueError('Identificador o formato inválido.')
                    if not isinstance(item.get('title'), str) or not item['title'].strip() or len(item['title']) > 200:
                        raise ValueError('Título inválido.')
                    if any(p.is_symlink() for p in (folder/'learning', folder/'learning/learning.sqlite3', folder/'assets')) or not (folder/'learning/learning.sqlite3').is_file() or not (folder/'assets').is_dir():
                        raise ValueError('Faltan los datos del pliego o contienen enlaces simbólicos.')
                    entries.append({'id': item['id'], 'title': item['title'], 'path': str(folder)})
                elif (folder/'manifest.json').is_file() and (folder/'snapshot.json').is_file():
                    backups.append({'title': folder.name, 'folder': str(folder)})
            except (ValueError, OSError, TypeError) as exc:
                warnings.append(folder.name+': '+str(exc))
    found = {}
    ambiguous = set()
    for item in entries:
        if item['id'] in found:
            ambiguous.add(item['id'])
        found[item['id']] = item
    for item in registry(data):
        # Legacy registries and paths remain valid after the UI rename.
        item = {**item, 'path': item.get('path', str(Path(data)/'rooms'/item['id']))}
        if (Path(item['path'])/'learning/learning.sqlite3').is_file():
            if item['id'] in found and Path(item['path']).resolve() != Path(found[item['id']]['path']).resolve():
                ambiguous.add(item['id'])
            elif item['id'] not in found:
                found[item['id']] = item
    for duplicate in ambiguous:
        found.pop(duplicate, None)
        warnings.append('ID de pliego duplicado: '+duplicate+'. No se abrirá ninguna de esas copias.')
    return {'margen': location, 'pliegos': list(found.values()), 'backups': backups, 'warnings': warnings}


def initialize(scope):
    import server
    with LOCK:
        if not (scope['data']/'learning.sqlite3').exists():
            scope['data'].mkdir(parents=True, exist_ok=True)
            token = server.ACTIVE_WORKSPACE.set(scope)
            try:
                server.init_db()
            finally:
                server.ACTIVE_WORKSPACE.reset(token)
    return scope


def create(data, root, title):
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError('Indicá un nombre de pliego de hasta 200 caracteres.')
    with LOCK:
        directory = Path(margen(data)['path'])
        if not directory.is_dir():
            raise ValueError('La carpeta del Margen no está disponible.')
        pliego_id = 'pliego-'+uuid.uuid4().hex
        with tempfile.TemporaryDirectory(prefix='.create-', dir=directory) as temp:
            stage = Path(temp)/'pliego'
            stage.mkdir(); (stage/'assets').mkdir()
            item = {'format': 'glosa-pliego', 'version': 1, 'id': pliego_id, 'title': title.strip()}
            initialize({**item, 'data': stage/'learning', 'root': stage/'assets'})
            (stage/'pliego.json').write_text(json.dumps(item, ensure_ascii=False, indent=2)+'\n')
            stage.rename(directory/pliego_id)
    return {'id': pliego_id, 'title': title.strip()}


def registry(data):
    path = Path(data)/'rooms.json'
    return json.loads(path.read_text()) if path.exists() else []


def room(data, root, room_id):
    if room_id == 'local':
        return {'id': 'local', 'title': 'Pliego local', 'data': Path(data), 'root': Path(root)}
    if room_id == TUTORIAL_ID:
        return initialize({'id': TUTORIAL_ID, 'title': 'Primer trazo', 'kind': 'tutorial', 'data': Path(data)/'tutorial', 'root': Path(root)})
    for item in inventory(data, root)['pliegos']:
        if item['id'] == room_id:
            base = Path(item['path'])
            return {**item, 'data': base/'learning', 'root': base/'assets'}
    raise ValueError('Pliego no disponible. Abrí Margen para elegir otro.')


def list_rooms(data, root):
    return [{'id': item['id'], 'title': item['title']}
            for item in [{'id': TUTORIAL_ID, 'title': 'Primer trazo', 'kind': 'tutorial'}, room(data, root, 'local'), *inventory(data, root)['pliegos']]]


def register(bundle, data, root, title=''):
    from scripts.room_backup import restore_room, verify_bundle
    if not isinstance(title, str):
        raise ValueError('Nombre de pliego inválido.')
    state, _ = verify_bundle(bundle)
    title = title.strip() or ' / '.join(c['title'] for c in state['courses'])
    if not title or len(title) > 200:
        raise ValueError('Nombre de pliego inválido.')
    with LOCK:
        room_id = 'room-'+uuid.uuid4().hex
        directory = Path(margen(data)['path'])
        if not directory.is_dir():
            raise ValueError('La carpeta del Margen no está disponible.')
        with tempfile.TemporaryDirectory(prefix='.import-', dir=directory) as temp:
            stage = Path(temp)/'room'
            stage.mkdir()
            (stage/'assets').mkdir()
            restore_room(bundle, stage/'learning', stage/'assets')
            (stage/'pliego.json').write_text(json.dumps({'format': 'glosa-pliego', 'version': 1, 'id': room_id, 'title': title}, ensure_ascii=False, indent=2)+'\n')
            target = directory/room_id
            stage.rename(target)
            items = registry(data)
            item = {'id': room_id, 'title': title, 'path': str(target)}
            items.append(item)
            pending = Path(data)/'rooms.json.tmp'
            try:
                pending.write_text(json.dumps(items, ensure_ascii=False, indent=2)+'\n')
                pending.replace(Path(data)/'rooms.json')
            except Exception:
                shutil.rmtree(target)
                raise
    return item


def import_zip(encoded, data, root, title=''):
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        raise ValueError('ZIP inválido.') from None
    if len(raw) > 60_000_000:
        raise ValueError('El paquete admite hasta 60 MB comprimidos.')
    with tempfile.TemporaryDirectory(prefix='glosa-zip-') as temp:
        directory = Path(temp)
        archive = directory/'room.zip'
        archive.write_bytes(raw)
        bundle = directory/'bundle'
        bundle.mkdir()
        try:
            with zipfile.ZipFile(archive) as z:
                entries = z.infolist()
                if len(entries) > 3000 or sum(i.file_size for i in entries) > 250_000_000:
                    raise ValueError('ZIP demasiado grande al descomprimir.')
                seen = set()
                for item in entries:
                    name = item.filename
                    path = Path(name)
                    if path.is_absolute() or '..' in path.parts or '\\' in name or name in seen or (item.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError('Ruta o enlace inválido en ZIP.')
                    seen.add(name)
                    if item.is_dir():
                        continue
                    destination = bundle/path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(item) as source, destination.open('wb') as target:
                        shutil.copyfileobj(source, target)
        except zipfile.BadZipFile:
            raise ValueError('ZIP inválido.') from None
        return register(bundle, data, root, title)


def export_zip(data, root):
    from scripts.room_backup import export_room
    with tempfile.TemporaryDirectory(prefix='glosa-download-') as temp:
        bundle = Path(temp)/'bundle'
        export_room(bundle, data, root)
        archive = Path(temp)/'sala.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            for file in sorted(bundle.rglob('*')):
                if file.is_file():
                    z.write(file, file.relative_to(bundle).as_posix())
        if archive.stat().st_size > 60_000_000:
            raise ValueError('La sala supera 60 MB: exportala por carpeta con room_backup.py.')
        return archive.read_bytes()
