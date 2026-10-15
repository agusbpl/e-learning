"""Portable Glosa workspace backup, without credentials or a live SQLite file.

One room is exported in full, including its library and all its courses.
Restore only into an empty data directory, never over an existing study history.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@contextmanager
def workspace(root, data):
    # Importing the server must not create/use the user's default data directory.
    if 'server' not in sys.modules:
        previous = os.environ.get('LEARNING_DATA_DIR')
        os.environ['LEARNING_DATA_DIR'] = str(data)
        try:
            import server
        finally:
            if previous is None:
                os.environ.pop('LEARNING_DATA_DIR', None)
            else:
                os.environ['LEARNING_DATA_DIR'] = previous
    else:
        import server
    token = server.ACTIVE_WORKSPACE.set({'root': root, 'data': data, 'id': 'portable'})
    try:
        yield server
    finally:
        server.ACTIVE_WORKSPACE.reset(token)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def asset_path(doc):
    filename, doc_id = doc['filename'], doc['id']
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', doc_id):
        raise ValueError('ID de documento inválido.')
    if Path(filename).name != filename or not filename.endswith('.pdf'):
        raise ValueError('Nombre de PDF inválido.')
    if doc['storage'] not in ('source', 'upload'):
        raise ValueError('Almacenamiento inválido.')
    prefix = 'root/sources' if doc['storage'] == 'source' else 'data/documents'
    cache_prefix = 'root/.md_cache' if doc['storage'] == 'source' else prefix
    return prefix+'/'+filename, cache_prefix+'/'+doc_id+'.json'


def export_room(output, data, root=ROOT):
    output, data, root = Path(output).resolve(), Path(data).resolve(), Path(root).resolve()
    if output.exists():
        raise ValueError('El destino ya existe. Usá una carpeta nueva para cada respaldo.')
    if not (data/'learning.sqlite3').is_file():
        raise ValueError('No existe una base de estudio para exportar.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='glosa-export-') as temp:
        frozen = Path(temp)/'database'
        frozen.mkdir()
        # SQLite backup API takes a consistent snapshot while the app stays running.
        with sqlite3.connect('file:'+str(data/'learning.sqlite3')+'?mode=ro', uri=True) as source:
            with sqlite3.connect(frozen/'learning.sqlite3') as dest:
                source.backup(dest)
        with workspace(root, frozen) as server:
            state = server.snapshot()
            state.pop('tutorConnected', None)
            diary = server.markdown_export(state)
        stage = Path(temp)/'bundle'
        stage.mkdir()
        write_json(stage/'snapshot.json', state)
        (stage/'diario.md').write_text(diary, encoding='utf-8')
        for doc in state['library']['documents']:
            pdf, cache = asset_path(doc)
            for name in (pdf, cache):
                prefix, relative = name.split('/', 1)
                source = (root if prefix == 'root' else data)/relative
                if not source.is_file():
                    if name == cache:
                        continue  # Some documents have no extracted text (e.g. scans).
                    raise ValueError('Falta el PDF: '+doc['title'])
                if name == pdf and digest(source) != doc['sha256']:
                    raise ValueError('El PDF difiere de su registro: '+doc['title'])
                dest = stage/name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, dest)
        source_manifest = [dict(id=d['id'], title=d['title'], sha256=d['sha256'],
                                url='/sources/'+d['filename'], pages=d.get('pages'),
                                cache=d['id']+'.json')
                           for d in state['library']['documents'] if d['storage'] == 'source']
        write_json(stage/'root/.md_cache/manifest.json', source_manifest)
        from library import note_markdown
        for index, note in enumerate(state['library']['notes'], 1):
            path = stage/'apuntes'/(str(index)+'.md')
            path.parent.mkdir(exist_ok=True)
            path.write_text(note_markdown(note, state['library']['documents']), encoding='utf-8')
        (stage/'README.md').write_text('''# Pliego · Glosa

Respaldo privado completo. `snapshot.json` conserva cursos, notas, versiones,
respuestas, conversaciones, contexto, calendario y preferencias. `root/` y `data/`
incluyen PDFs y texto extraído. `apuntes/` y `diario.md` son vistas legibles.
No contiene claves de API. Tampoco borradores que solo estén en el navegador.

## Abrir en otra computadora

Requiere Python 3.11 o posterior y una copia de Glosa. Conservá este respaldo
en una carpeta privada fuera del código de la aplicación:

```bash
git clone https://github.com/agusbpl/glosa.git
cd glosa
./start.sh
```

Abrí http://127.0.0.1:8765. Pulsá GLOSA → Margen → Importar un respaldo e indicá
la ruta absoluta de la carpeta que contiene `manifest.json` y `snapshot.json`.
Glosa valida e importa todo en un pliego independiente y la abre. También podés importar
un ZIP exportado desde Margen. `: → Abrir Margen` permite hacerlo con el teclado.
El pliego local previo se conserva; podés volver a ella desde el selector.
Para conectar el tutor, configurá tu proveedor y tu clave en Ajustes.
El lector y los apuntes funcionan sin el tutor. Para adjuntar PDFs nuevos o usar
el MCP, instalá `requirements-author.txt` en `.venv-author` según el README del código.

## Volver con el progreso

Con el código actualizado, exportá a una carpeta nueva:

```bash
python3 scripts/room_backup.py export ../sala-nueva
```

Transferí la nueva carpeta por un canal privado e importala desde Margen en la
otra PC. Revisá su contenido antes de compartirla. La herramienta no sobrescribe
historiales ni fusiona notas simultáneas. No subas este respaldo al repositorio
público del código.
''', encoding='utf-8')
        files = {p.relative_to(stage).as_posix(): {'sha256': digest(p), 'bytes': p.stat().st_size}
                 for p in stage.rglob('*') if p.is_file()}
        write_json(stage/'manifest.json', {'format': 'glosa-workspace', 'version': 1,
                                         'exportedAt': state['exportedAt'],
                                         'courseIds': [c['id'] for c in state['courses']], 'files': files})
        # Destination appears only once the entire bundle is ready.
        pending = output.parent/('.'+output.name+'-'+os.urandom(8).hex())
        try:
            shutil.copytree(stage, pending)
            pending.rename(output)
        finally:
            if pending.exists():
                shutil.rmtree(pending)
    return {'courses': len(state['courses']), 'documents': len(state['library']['documents']),
            'notes': len(state['library']['notes']), 'events': len(state['events'])}


def verify_bundle(bundle):
    bundle = Path(bundle).resolve()
    def read_object(name):
        path = bundle/name
        if not bundle.is_dir() or not path.is_file() or path.is_symlink():
            raise ValueError('Respaldo incompleto: falta '+name)
        try:
            value = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, ValueError):
            raise ValueError('No se pudo leer '+name+' como JSON de respaldo.') from None
        if not isinstance(value, dict):
            raise ValueError('Se requiere un objeto JSON en '+name)
        return value
    manifest = read_object('manifest.json')
    if manifest.get('format') != 'glosa-workspace' or manifest.get('version') != 1:
        raise ValueError('Formato de respaldo incompatible.')
    files = manifest.get('files')
    if not isinstance(files, dict) or 'snapshot.json' not in files:
        raise ValueError('Manifiesto incompleto.')
    allowed = re.compile(r'(snapshot\.json|diario\.md|README\.md|apuntes/[0-9]+\.md|'
                         r'root/sources/[^/]+\.pdf|root/\.md_cache/[A-Za-z0-9_.-]+\.json|'
                         r'data/documents/[A-Za-z0-9_.-]+\.(pdf|json))')
    for name, item in files.items():
        parts = PurePosixPath(name).parts
        if not allowed.fullmatch(name) or '..' in parts or '\\' in name:
            raise ValueError('Ruta de respaldo inválida.')
        if (not isinstance(item, dict) or type(item.get('bytes')) is not int
                or item['bytes'] < 0 or not isinstance(item.get('sha256'), str)
                or not re.fullmatch(r'[a-f0-9]{64}', item['sha256'])):
            raise ValueError('Metadatos de archivo inválidos en el respaldo.')
        path = bundle/name
        if any(p.is_symlink() for p in [path, *path.parents]) or not path.is_file():
            raise ValueError('Archivo faltante o enlace simbólico: '+name)
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError('Archivo alterado: '+name)
    state = read_object('snapshot.json')
    if manifest.get('courseIds') != [c['id'] for c in state['courses']]:
        raise ValueError('Los cursos no coinciden con el manifiesto.')
    for doc in state['library']['documents']:
        pdf, _ = asset_path(doc)
        if pdf not in files or files[pdf]['sha256'] != doc['sha256']:
            raise ValueError('PDF sin respaldo íntegro: '+doc['title'])
    return state, files


def restore_room(bundle, data, root=ROOT):
    bundle, data, root = Path(bundle).resolve(), Path(data).resolve(), Path(root).resolve()
    state, files = verify_bundle(bundle)
    if data.exists() and (not data.is_dir() or any(data.iterdir())):
        raise ValueError('La carpeta de datos debe estar vacía: no se sobrescribe el historial.')
    data.parent.mkdir(parents=True, exist_ok=True)
    for name, item in files.items():
        if name.startswith('root/'):
            destination = root/name[5:]
            if destination.exists() and (not destination.is_file() or digest(destination) != item['sha256']):
                raise ValueError('Archivo local distinto del respaldo: '+name)
            if any(p.is_symlink() for p in [destination, *destination.parents]):
                raise ValueError('Destino con enlaces simbólicos.')
    with tempfile.TemporaryDirectory(prefix='.glosa-restore-', dir=data.parent) as temp:
        stage = Path(temp)/'data'
        stage.mkdir()
        # Empty root avoids seeding an old course or importing unrelated local PDFs.
        empty_root = Path(temp)/'root'
        empty_root.mkdir()
        with workspace(empty_root, stage) as server:
            server.init_db()
            server.restore_snapshot(state)
            restored = server.snapshot()
        for key in ('courses', 'events', 'annotationRevisions', 'library', 'calendarEvents', 'settings'):
            if restored[key] != state[key]:
                raise ValueError('La restauración no conserva exactamente '+key)
        for name in files:
            if name.startswith('data/'):
                destination = stage/name[5:]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(bundle/name, destination)
        from library import note_markdown
        (stage/'notes').mkdir(exist_ok=True)
        for note in state['library']['notes']:
            # Existing validators accept IDs more broadly; never use them as paths.
            if not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', note['id']) or note['id'] in ('.', '..'):
                raise ValueError('ID de apunte inválido para su archivo Markdown.')
            (stage/'notes'/(note['id']+'.md')).write_text(
                note_markdown(note, state['library']['documents']), encoding='utf-8')
        for name in files:
            if name.startswith('root/'):
                destination = root/name[5:]
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    shutil.copyfile(bundle/name, destination)
        if data.exists():
            data.rmdir()
        stage.rename(data)
    return {'courses': len(state['courses']), 'documents': len(state['library']['documents']),
            'notes': len(state['library']['notes']), 'events': len(state['events'])}


def main():
    parser = argparse.ArgumentParser(description='Exportar/restaurar un entorno completo de Glosa.')
    parser.add_argument('action', choices=['export', 'restore', 'verify'])
    parser.add_argument('folder', type=Path)
    parser.add_argument('--data', type=Path, default=Path(os.environ.get('LEARNING_DATA_DIR', ROOT/'.local-data')))
    args = parser.parse_args()
    try:
        if args.action == 'verify':
            state, _ = verify_bundle(args.folder)
            result = {'courses': len(state['courses']), 'documents': len(state['library']['documents'])}
        else:
            result = (export_room if args.action == 'export' else restore_room)(args.folder, args.data)
        print(json.dumps({'ok': True, **result}, ensure_ascii=False))
    except (ValueError, KeyError, OSError, TypeError, sqlite3.Error) as exc:
        parser.exit(1, 'No se completó: '+str(exc)+'\n')


if __name__ == '__main__':
    main()
