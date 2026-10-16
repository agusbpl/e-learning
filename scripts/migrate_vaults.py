"""Migración segura de pliegos a un Margen visible (plan / dry-run / apply).

Reúne TODOS los pliegos —incluida la biblioteca local— en un Margen visible
(`~/Margen` por defecto) con subcarpetas de nombre humano, sin fusionar bases,
sin cambiar IDs y sin perder historial, PDFs, apuntes ni conversaciones.

Garantías:
- `plan`/`dry-run` son estrictamente de solo lectura: no crean el Margen, ni
  bases, ni carpetas; solo describen rutas, acciones y colisiones.
- `apply` exige un respaldo verificable FUERA del repositorio y sin claves
  (reutiliza `room_backup.export_room` + `verify_bundle`).
- Los traslados de pliego son `rename` atómicos en el mismo sistema de archivos;
  entre sistemas, copia verificada por hash a una carpeta temporal oculta y
  luego `rename` — el origen solo se borra tras coincidencia byte a byte.
- La metadata portable (`pliego.json`) se asegura ANTES de mover, así que un
  pliego legado importado (solo `assets`+`learning` y registro) nunca queda
  inaccesible. Los apuntes viven siempre en `<pliego>/Apuntes`.
- La biblioteca local se copia a una bóveda nueva con `id` estable `'local'` y
  un marcador; el original no se borra y solo se desactiva cuando el servidor
  integrado deja de usarlo. Si el original cambió después de la copia, el
  marcador se ignora: nunca se activa una copia vieja.
- Antes de mover, se captura una huella de contenido (IDs + sha256 de cursos,
  eventos, notas, versiones, documentos, calendario y config, más sha256 de
  cada archivo de `assets`) y se vuelve a comprobar después. También se
  preservan byte a byte los apuntes Markdown que ya existían en disco, incluso
  si `migrate_notes_to_files` agregó frontmatter a los recién exportados.
- Idempotente: volver a ejecutarla no duplica ni pisa nada. Colisiones de nombre
  entre pliegos planificados se resuelven con sufijo; una carpeta destino con
  OTRO contenido aborta ese pliego sin mezclar.
- Recuperable: bloqueo exclusivo `O_EXCL`, diario (journal) por pliego y
  `--recuperar` que solo limpia restos propios. Un pliego ya movido se
  redescubre por su `pliego.json`, nunca por el registro viejo.

No aplica datos reales por sí mismo: el orquestador lo ejecuta tras las pruebas.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import rooms
from library import Library
from scripts.room_backup import export_room, verify_bundle, visible_apuntes

LOCAL_TITLE = 'Biblioteca local'
STAGE_PREFIX = '.glosa-stage-'
LOCK_NAME = '.glosa-migracion.lock'
JOURNAL_NAME = 'migracion-journal.json'
REPORT_NAME = 'migracion-informe.json'
# Study-content tables whose IDs and bodies must survive a move byte for byte.
CONTENT_TABLES = ('courses', 'events', 'documents', 'notes', 'note_versions', 'course_drafts',
                  'annotation_revisions', 'note_tutor', 'tutor_contexts', 'calendar_events', 'config')


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def _counts(database):
    """Read-only row counts for the user-facing summary."""
    database = Path(database)
    if database.is_symlink() or not database.is_file():
        return None
    try:
        connection = sqlite3.connect(database.resolve().as_uri()+'?mode=ro', uri=True, timeout=2)
    except (sqlite3.Error, OSError):
        return None
    counts = {}
    try:
        for key, query in rooms.CONTENTS_QUERIES:
            try:
                counts[key] = connection.execute(query).fetchone()[0]
            except sqlite3.Error:
                counts[key] = None
        return counts
    finally:
        connection.close()


def _table_fingerprint(database):
    """id + sha256(body) for every study table; counts alone are not enough."""
    database = Path(database)
    if database.is_symlink() or not database.is_file():
        return None
    try:
        connection = sqlite3.connect(database.resolve().as_uri()+'?mode=ro', uri=True, timeout=5)
    except (sqlite3.Error, OSError):
        return None
    fingerprint = {}
    try:
        for table in CONTENT_TABLES:
            try:
                rows = connection.execute('SELECT id, body FROM '+table).fetchall()
            except sqlite3.Error:
                continue
            fingerprint[table] = sorted(
                [str(row[0]), hashlib.sha256(str(row[1]).encode('utf-8')).hexdigest()] for row in rows)
        return fingerprint
    finally:
        connection.close()


def _fingerprint_hash(fingerprint):
    return hashlib.sha256(json.dumps(fingerprint, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def _tree_digests(folder):
    folder = Path(folder)
    result = {}
    if not folder.exists():
        return result
    for base, dirs, names in os.walk(folder, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(base)/d).is_symlink()]
        for name in names:
            entry = Path(base)/name
            if entry.is_symlink():
                raise ValueError('La carpeta contiene enlaces simbólicos: '+str(entry))
            result[entry.relative_to(folder).as_posix()] = (entry.stat().st_size, digest(entry))
    return result


def _inside(path, folder):
    try:
        path, folder = Path(path).resolve(), Path(folder).resolve()
    except OSError:
        return False
    return path == folder or folder in path.parents


def _is_pliego(folder):
    metadata = Path(folder)/'pliego.json'
    if metadata.is_symlink() or not metadata.is_file():
        return False
    try:
        item = json.loads(metadata.read_text())
    except (OSError, ValueError):
        return False
    return item.get('format') == 'glosa-pliego' and item.get('version') == 1 and isinstance(item.get('id'), str)


def _write_pliego(folder, pliego_id, title):
    """Atomic portable metadata at the vault root."""
    folder = Path(folder)
    item = {'format': 'glosa-pliego', 'version': 1, 'id': pliego_id, 'title': title}
    pending = folder/'.pliego.json.tmp'
    pending.write_text(json.dumps(item, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    pending.replace(folder/'pliego.json')


def _assigned_folder_name(name, desired):
    """¿`name` ya es el nombre humano único asignado a `desired`?

    Acepta el nombre base y sus variantes numeradas `base (2)`, `base (3)`…
    que `_reserve` produce al resolver colisiones entre títulos iguales. Así un
    pliego que ya recibió un sufijo no se sigue renombrando en cada plan
    (renombrado infinito) y conserva su carpeta estable.

    Un nombre opaco (el ID del pliego, p. ej. `pliego-…`/`room-…`) no coincide
    con el nombre humano, por lo que la carpeta sigue renombrándose a humano.
    """
    if str(name).casefold() == str(desired).casefold():
        return True
    match = re.fullmatch(re.escape(desired)+r' \((\d+)\)', str(name), flags=re.IGNORECASE)
    return match is not None and int(match.group(1)) >= 2


def _reserve(directory, name, taken):
    candidate, number = name, 2
    while True:
        key = candidate.casefold()
        if key not in taken and not (directory/candidate).exists():
            taken.add(key)
            return directory/candidate
        candidate = f'{name} ({number})'
        number += 1
        if number > 9999:
            raise ValueError('No se pudo encontrar un nombre libre en el Margen destino.')


def _scan_vaults(directory):
    """Valid pliego folders directly inside `directory` (read-only, no symlinks)."""
    found = {}
    directory = Path(directory)
    if not directory.is_dir():
        return found
    for folder in sorted(directory.iterdir()):
        if folder.is_symlink() or not folder.is_dir() or folder.name.startswith('.') or not _is_pliego(folder):
            continue
        item = json.loads((folder/'pliego.json').read_text())
        if item['id'] in found:
            raise ValueError('Dos carpetas del Margen destino comparten el ID '+item['id']+'. Resolvé la colisión antes de migrar.')
        found[item['id']] = {'id': item['id'], 'title': item.get('title') or item['id'], 'path': str(folder)}
    return found


def plan_migration(data, root, target=None, include_local=True, local_name=LOCAL_TITLE):
    """Describe the migration without touching the disk. Returns a serializable dict.

    Read-only: uses `rooms.margen(..., create=False)` and read-only discovery, so
    it never creates `~/Margen`, a database or a folder. Existing vaults already
    inside the target are only *renamed* when their folder name is not human.
    """
    data, root = Path(data).resolve(), Path(root).resolve()
    target = Path(target).expanduser().resolve() if target else (Path.home()/rooms.DEFAULT_MARGEN_NAME)
    location = rooms.margen(data, create=False)
    inventory = rooms.inventory(data, root, details=False, create=False)
    moved_here = _scan_vaults(target)
    # The local alias vault is not a pliego: it is handled by the local branch.
    moved_here.pop(rooms.LOCAL_ID, None)
    sources = {Path(entry['path']).resolve() for entry in inventory['pliegos']}
    taken = set()
    if target.is_dir():
        for folder in target.iterdir():
            if folder.is_dir() and not folder.is_symlink():
                taken.add(folder.name.casefold())
    items, collisions = [], []
    seen = set()

    def clash(item_id, title, folder, reason=None):
        collisions.append({'id': item_id, 'title': title,
                           'reason': reason or ('La carpeta destino ya existe con otro contenido: '+str(folder))})

    # L4: un ID presente en dos ubicaciones (p. ej. copia cross-device ya completa
    # en el Margen y el origen que quedó a medio borrar) se bloquea y se registra;
    # nada se mueve ni se borra a ciegas.
    for duplicate, paths in sorted(inventory.get('duplicates', {}).items()):
        if duplicate in (rooms.LOCAL_ID, rooms.TUTORIAL_ID):
            continue
        collisions.append({'id': duplicate, 'title': duplicate,
                           'reason': 'El ID '+duplicate+' existe en dos ubicaciones y debe resolverse antes de mover: '
                                     + ', '.join(paths)+'. No se moverá ni borrará ninguna a ciegas.'})

    for entry in inventory['pliegos']:
        source, item_id, title = Path(entry['path']), entry['id'], entry['title']
        seen.add(item_id)
        desired = rooms.safe_folder_name(title)
        already = moved_here.get(item_id)
        busy = target/desired
        if already is not None and Path(already['path']).resolve() != source.resolve():
            clash(item_id, title, already['path'], 'Ya existe un pliego con el mismo ID en el Margen destino; no se duplica.')
            continue
        if source.parent == target and _assigned_folder_name(source.name, desired):
            dest, action = source, 'none'
        elif busy.exists() and busy.resolve() not in sources and not _is_pliego(busy):
            clash(item_id, title, busy)
            continue
        else:
            dest = _reserve(target, desired, taken)
            action = 'move' if dest != source else 'none'
        if _inside(target, source) and target != source.parent:
            clash(item_id, title, source, 'El destino está dentro del pliego de origen.')
            continue
        taken.add(dest.name.casefold())
        items.append({'kind': 'pliego', 'id': item_id, 'title': title,
                      'from': str(source), 'to': str(dest), 'action': action,
                      'metadata': _is_pliego(source),
                      'counts': _counts(source/'learning/learning.sqlite3')})
    # Vaults already inside the target (e.g. a previous run reached them before
    # stopping) are reported as unchanged instead of disappearing from the plan.
    for item_id, already in sorted(moved_here.items()):
        if item_id in seen:
            continue
        items.append({'kind': 'pliego', 'id': item_id, 'title': already['title'],
                      'from': already['path'], 'to': already['path'], 'action': 'none',
                      'metadata': True,
                      'counts': _counts(Path(already['path'])/'learning/learning.sqlite3')})

    source_db = data/'learning.sqlite3'
    local = None
    if include_local and source_db.is_file() and not source_db.is_symlink():
        probe = rooms.local_scope(data)
        if probe is not None:
            taken.add(Path(probe['path']).name.casefold())
            local = {'kind': 'local', 'id': 'local', 'title': local_name,
                     'from': str(data), 'to': probe['path'], 'action': 'none', 'counts': _counts(source_db)}
        else:
            desired = rooms.safe_folder_name(local_name)
            busy = target/desired
            if busy.exists() and busy.resolve() != data and not _is_pliego(busy):
                clash('local', local_name, busy)
            else:
                dest = _reserve(target, desired, taken)
                local = {'kind': 'local', 'id': 'local', 'title': local_name,
                         'from': str(data), 'to': str(dest), 'action': 'copy',
                         'counts': _counts(source_db), 'database': str(source_db)}
    result = {'format': 'glosa-migracion', 'version': 1,
              'margenActual': location['path'], 'margenSource': location['source'],
              'target': str(target), 'items': items, 'local': local,
              'warnings': inventory['warnings'], 'collisions': collisions}
    if target != Path(location['path']).resolve():
        result['actions'] = ['crear Margen destino', 'actualizar margen.json']
    return result


# --- apply helpers -----------------------------------------------------------

def _ensure_backup(bundle, action):
    """Export + verify once; reuse an already-verified bundle (idempotent)."""
    bundle = Path(bundle)
    if bundle.exists():
        state, files = verify_bundle(bundle)
    else:
        if action is None:
            raise ValueError('Falta el respaldo y no hay origen para recrearlo: '+str(bundle))
        data, root = action
        export_room(bundle, data, root)
        state, files = verify_bundle(bundle)
    for name in files:
        if Path(name).name == 'tutor-credentials.json':
            raise ValueError('El respaldo no puede contener credenciales.')
    return {'path': str(bundle), 'files': len(files),
            'counts': {'courses': len(state['courses']), 'documents': len(state['library']['documents']),
                       'notes': len(state['library']['notes']), 'events': len(state['events'])}}


def _move_folder(source, destination):
    """Atomic within one filesystem; verified copy-then-delete across devices."""
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise ValueError('El destino ya existe: '+str(destination))
    try:
        source.rename(destination)
        return 'rename'
    except OSError:
        pass
    stage = destination.parent/(STAGE_PREFIX+uuid.uuid4().hex[:10])
    try:
        shutil.copytree(source, stage, symlinks=False)
        if _tree_digests(source) != _tree_digests(stage):
            raise ValueError('La copia no coincide con el origen; no se borró nada.')
        stage.rename(destination)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    shutil.rmtree(source)
    return 'copy'


def _absorb_legacy_notes(vault):
    """Move notes that predate the visible root (`learning/Apuntes`) to `<vault>/Apuntes`."""
    vault = Path(vault)
    legacy, root = vault/'learning'/'Apuntes', vault/'Apuntes'
    if legacy.is_dir() and not legacy.is_symlink() and legacy.resolve() != root.resolve():
        for entry in sorted(legacy.rglob('*')):
            if entry.is_symlink() or not entry.is_file():
                continue
            rel = entry.relative_to(legacy)
            destination = root/rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                if destination.read_bytes() != entry.read_bytes():
                    destination = destination.parent/(destination.stem+'.legacy'+destination.suffix)
            shutil.copy2(entry, destination)
        shutil.rmtree(legacy, ignore_errors=True)
    mirrors = vault/'learning'/'notes'
    if mirrors.is_dir() and not mirrors.is_symlink():
        target = vault/'notes-legacy'
        target.mkdir(parents=True, exist_ok=True)
        for entry in sorted(mirrors.iterdir()):
            if entry.is_file() and not entry.is_symlink() and not (target/entry.name).exists():
                shutil.copy2(entry, target/entry.name)
        shutil.rmtree(mirrors, ignore_errors=True)


def _materialize_notes(vault, notes_root=None):
    """SQLite → archivos en `<vault>/Apuntes`, preservando byte a byte los originales.

    Los apuntes que ya existían en disco son la fuente (edición externa incluida):
    se guardan, se exporta lo que solo vivía en la base y se vuelven a dejar los
    originales encima, de modo que la migración agrega archivos faltantes sin
    pisar texto editado a mano.
    """
    vault = Path(vault)
    root = Path(notes_root) if notes_root is not None else vault/'Apuntes'
    root.mkdir(parents=True, exist_ok=True)
    preserved = tempfile.mkdtemp(prefix='glosa-notas-')
    try:
        shutil.copytree(root, Path(preserved)/'Apuntes', dirs_exist_ok=True)
        report = Library(vault/'learning/learning.sqlite3', vault/'learning', vault/'assets', notes_dir=root).migrate_notes_to_files()
        shutil.copytree(Path(preserved)/'Apuntes', root, dirs_exist_ok=True)
        return report
    finally:
        shutil.rmtree(preserved, ignore_errors=True)


def _local_assets(data, root, destination):
    """Copy uploaded PDFs, course sources and their caches into the new vault."""
    data, root, destination = Path(data), Path(root), Path(destination)
    for name in ('documents',):
        origin = data/name
        if not origin.is_dir() or origin.is_symlink():
            continue
        for entry in sorted(origin.iterdir()):
            if entry.is_symlink() or not entry.is_file():
                continue
            target = destination/name/entry.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, target)
    for name, folder in (('sources', root/'sources'), ('.md_cache', root/'.md_cache')):
        if not folder.is_dir() or folder.is_symlink():
            continue
        for entry in sorted(folder.iterdir()):
            if entry.is_symlink() or not entry.is_file():
                continue
            target = destination/name/entry.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, target)


def _stage_local(data, root, stage, title):
    """Build the 'local' pliego copy: consistent DB, PDFs, caches and Apuntes."""
    data, root, stage = Path(data), Path(root), Path(stage)
    (stage/'learning').mkdir(parents=True)
    (stage/'assets').mkdir(parents=True)
    source_db = data/'learning.sqlite3'
    before = source_db.stat()
    destination = stage/'learning'/'learning.sqlite3'
    with sqlite3.connect('file:'+str(source_db.resolve())+'?mode=ro', uri=True) as src:
        with sqlite3.connect(destination) as dst:
            src.backup(dst)
    after = source_db.stat()
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise ValueError('La biblioteca local cambió durante la copia; cerrala y volvé a intentar.')
    # L2: la instantánea SQLite debe conservar IDs y cuerpos exactos del origen.
    source_fingerprint = _table_fingerprint(source_db)
    if source_fingerprint is not None and _table_fingerprint(destination) != source_fingerprint:
        raise ValueError('La copia de la base local no coincide con el origen (IDs/cuerpos); no se migró nada.')
    _local_assets(data, root, stage/'assets')
    # L2: PDFs, fuentes y cachés copiados byte a byte, no solo contados.
    for name, folder in (('documents', data/'documents'), ('sources', root/'sources'), ('.md_cache', root/'.md_cache')):
        if not folder.is_dir() or folder.is_symlink():
            continue
        for entry in sorted(folder.iterdir()):
            if entry.is_symlink() or not entry.is_file():
                continue
            target = stage/'assets'/name/entry.name
            if not target.is_file() or digest(target) != digest(entry):
                raise ValueError('Un PDF/caché de la biblioteca local no se copió íntegro: '+entry.name)
    _materialize_notes(stage, notes_root=stage/'Apuntes')
    # Authoritative on-disk originals win over the SQLite export.
    visible = visible_apuntes(data)
    if visible.is_dir() and not visible.is_symlink():
        for entry in sorted(visible.rglob('*')):
            if entry.is_symlink() or not entry.is_file():
                continue
            target = stage/'Apuntes'/entry.relative_to(visible)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, target)
    legacy = data/'notes'
    if legacy.is_dir() and not legacy.is_symlink():
        for entry in sorted(legacy.iterdir()):
            if entry.is_symlink() or not entry.is_file():
                continue
            target = stage/'notes-legacy'/entry.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, target)
    _write_pliego(stage, rooms.LOCAL_ID, title)
    return {'counts': _counts(source_db), 'original': {'bytes': after.st_size, 'mtimeNs': after.st_mtime_ns},
            'fingerprint': _table_fingerprint(stage/'learning/learning.sqlite3'),
            'assets': _tree_digests(stage/'assets')}


def _update_registry(data, moves):
    items = rooms.registry(data)
    if not items or not moves:
        return False
    changed = False
    updated = []
    for entry in items:
        if entry.get('id') in moves:
            updated.append({**entry, 'path': moves[entry['id']]})
            changed = True
        else:
            updated.append(entry)
    if not changed:
        return False
    pending = Path(data)/'rooms.json.tmp'
    pending.write_text(json.dumps(updated, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    pending.replace(Path(data)/'rooms.json')
    return True


def _write_margen(data, target):
    pending = Path(data)/'margen.json.tmp'
    pending.write_text(json.dumps({'path': str(target)}, ensure_ascii=False)+'\n', encoding='utf-8')
    pending.replace(Path(data)/'margen.json')


def _read_journal(target):
    path = Path(target)/JOURNAL_NAME
    if not path.is_file() or path.is_symlink():
        return {'format': 'glosa-migracion-journal', 'version': 1, 'done': [], 'status': 'nuevo'}
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'format': 'glosa-migracion-journal', 'version': 1, 'done': [], 'status': 'ilegible'}
    if not isinstance(value, dict) or not isinstance(value.get('done'), list):
        return {'format': 'glosa-migracion-journal', 'version': 1, 'done': [], 'status': 'ilegible'}
    return value


def _write_journal(target, journal):
    pending = Path(target)/(JOURNAL_NAME+'.tmp')
    pending.write_text(json.dumps(journal, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    pending.replace(Path(target)/JOURNAL_NAME)


def _acquire_lock(target, recovery):
    target = Path(target)
    lock = target/LOCK_NAME
    stages = sorted(target.glob(STAGE_PREFIX+'*')) if target.is_dir() else []
    if not recovery and (lock.exists() or stages):
        raise ValueError('Hay una migración en curso o interrumpida en '+str(target)+'. Revisá el informe y usá --recuperar.')
    if recovery:
        for stale in stages:
            shutil.rmtree(stale, ignore_errors=True)
        lock.unlink(missing_ok=True)
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('Otra migración tomó el bloqueo; esperá y volvé a intentar.') from None
    try:
        os.write(handle, json.dumps({'pid': os.getpid(), 'at': time.strftime('%Y-%m-%dT%H:%M:%S')}).encode('utf-8'))
    finally:
        os.close(handle)
    return lock


def _reconcile_vault(vault, notes_root=None):
    """Importa ediciones/borrados externos a SQLite ANTES de capturar la huella.

    B1: la materialización posterior importa la edición externa a `notes`; si se
    captura la huella antes, esa importación legítima parece "contenido cambiado"
    y aborta el traslado. Reconciliar primero (y marcar los borrados) deja la
    huella estable frente a la materialización. La identidad del archivo no se
    reformatea: `reconcile_notes` respeta el formato y no pisa texto ajeno.
    """
    vault = Path(vault)
    db = vault/'learning/learning.sqlite3'
    if not db.is_file() or db.is_symlink():
        return
    root = Path(notes_root) if notes_root is not None else vault/'Apuntes'
    Library(db, vault/'learning', vault/'assets', notes_dir=root).reconcile_notes()


def _apply_pliego(item, backup, journal, report):
    """Move (or confirm) one pliego, verifying IDs/content and materializing notes."""
    source, destination = Path(item['from']), Path(item['to'])
    record = _ensure_backup(backup/'pliegos'/item['id'],
                            (source/'learning', source/'assets') if source.is_dir() else None)
    if item['action'] == 'move' and source.is_dir():
        if not _is_pliego(source):
            _write_pliego(source, item['id'], item['title'])  # metadata before moving
        _absorb_legacy_notes(source)
        _reconcile_vault(source, source/'Apuntes')  # B1: edición externa antes de la huella
        fingerprint = _table_fingerprint(source/'learning/learning.sqlite3')
        assets = _tree_digests(source/'assets')
        algorithm = _move_folder(source, destination)
    else:
        _reconcile_vault(destination, destination/'Apuntes')
        fingerprint, assets, algorithm = _table_fingerprint(destination/'learning/learning.sqlite3'), _tree_digests(destination/'assets'), 'none'
    _materialize_notes(destination)
    after = _table_fingerprint(destination/'learning/learning.sqlite3')
    if fingerprint is not None and after != fingerprint:
        raise ValueError('El contenido de «'+item['title']+'» cambió durante el traslado; se detiene para revisarlo.')
    if assets and _tree_digests(destination/'assets') != assets:
        raise ValueError('Los archivos (PDFs/cachés) de «'+item['title']+'» cambiaron durante el traslado.')
    journal['done'].append({'kind': 'pliego', 'id': item['id'], 'to': str(destination), 'at': time.strftime('%Y-%m-%dT%H:%M:%S')})
    _write_journal(destination.parent, journal)
    entry = {**item, 'result': 'sin cambios' if item['action'] == 'none' else 'trasladado',
             'algorithm': algorithm, 'backup': record, 'verifiedCounts': _counts(destination/'learning/learning.sqlite3'),
             'fingerprint': _fingerprint_hash(after) if after is not None else None}
    report['pliegos'].append(entry)
    return str(destination)


def _apply_local(local, data, root, target, backup, report):
    if local['action'] == 'none':
        report['local'] = {**local, 'result': 'sin cambios'}
        return Path(local['to'])
    destination = Path(local['to'])
    record = _ensure_backup(backup/'local', (data, root))
    stage = Path(target)/(STAGE_PREFIX+uuid.uuid4().hex[:10])
    moved = False
    try:
        staged = _stage_local(data, root, stage, local['title'])
        if destination.exists():
            raise ValueError('El destino de la biblioteca local ya existe: '+str(destination))
        stage.rename(destination)
        moved = True
        # L2: el punto final debe conservar la huella de la instantánea verificada.
        moved_fp = _table_fingerprint(destination/'learning/learning.sqlite3')
        if staged.get('fingerprint') is not None and moved_fp != staged['fingerprint']:
            raise ValueError('La biblioteca local migrada no conserva IDs/cuerpos; se conserva el original.')
        if _tree_digests(destination/'assets') != staged.get('assets'):
            raise ValueError('Los PDFs de la biblioteca local migrada cambiaron; se conserva el original.')
    except Exception:
        if moved:
            shutil.rmtree(destination, ignore_errors=True)  # copia no verificada; el original queda intacto
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
    source_db = Path(data)/'learning.sqlite3'
    if _counts(source_db) != staged['counts']:
        raise ValueError('La biblioteca local cambió durante la copia; se conserva el original.')
    marker = {'format': 'glosa-local-alias', 'version': 1, 'id': rooms.LOCAL_ID, 'title': local['title'],
              'path': str(destination), 'original': staged['original'], 'at': time.strftime('%Y-%m-%dT%H:%M:%S')}
    pending = data/(rooms.LOCAL_ALIAS_FILE+'.tmp')
    pending.write_text(json.dumps(marker, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    pending.replace(data/rooms.LOCAL_ALIAS_FILE)
    report['local'] = {**local, 'result': 'copiado', 'backup': record, 'verifiedCounts': staged['counts']}
    return destination


def apply_migration(data, root, target, backup, include_local=True, local_name=LOCAL_TITLE, recovery=False):
    """Execute the plan. Refuses without a verifiable backup outside the repository."""
    data, root = Path(data).resolve(), Path(root).resolve()
    if backup is None:
        raise ValueError('Indicá --respaldo con una carpeta fuera del repositorio para el respaldo verificable.')
    backup = Path(backup).expanduser().resolve()
    if _inside(backup, ROOT):
        raise ValueError('La carpeta de respaldo debe estar fuera del repositorio.')
    current = plan_migration(data, root, target, include_local, local_name)
    target = Path(current['target'])
    if current['collisions']:
        raise ValueError('Hay colisiones que deben resolverse antes de aplicar: '+json.dumps(current['collisions'], ensure_ascii=False))
    target.mkdir(parents=True, exist_ok=True)
    lock = _acquire_lock(target, recovery)
    journal = _read_journal(target)
    journal['status'] = 'aplicando'
    journal['target'] = str(target)
    _write_journal(target, journal)
    done = {entry.get('id') for entry in journal['done'] if isinstance(entry, dict)}
    report = {'format': 'glosa-migracion-informe', 'version': 1, 'at': time.strftime('%Y-%m-%dT%H:%M:%S'),
              'target': str(target), 'backup': str(backup), 'profile': 'apply',
              'pliegos': [], 'local': None, 'registryUpdated': False, 'margenUpdated': False, 'problems': []}
    moves = {}
    try:
        for item in current['items']:
            if item['id'] in done and (Path(item['to'])/'pliego.json').is_file():
                moves[item['id']] = item['to']
                report['pliegos'].append({**item, 'result': 'ya aplicado (journal)'})
                continue
            moves[item['id']] = _apply_pliego(item, backup, journal, report)
        if current['local'] is not None:
            _apply_local(current['local'], data, root, target, backup, report)
        if Path(rooms.margen(data, create=False)['path']).resolve() != target.resolve():
            _write_margen(data, target)
            report['margenUpdated'] = True
        if _update_registry(data, moves):
            report['registryUpdated'] = True
        problems = verify_migration(data, root, target, include_local=include_local)
        report['verify'] = problems
        report['problems'] = problems['problems']
        journal['status'] = 'completo'
        _write_journal(target, journal)
        (backup).mkdir(parents=True, exist_ok=True)
        (backup/REPORT_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        if problems['problems']:
            raise ValueError('La verificación posterior falló: '+json.dumps(problems['problems'], ensure_ascii=False))
        (target/JOURNAL_NAME).unlink(missing_ok=True)
        return report
    except Exception:
        journal['status'] = 'incompleto'
        try:
            _write_journal(target, journal)
            (backup).mkdir(parents=True, exist_ok=True)
            (backup/REPORT_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        except OSError:
            pass
        raise
    finally:
        lock.unlink(missing_ok=True)


def verify_migration(data, root, target, include_local=True):
    """Post-conditions: valid pliegos, IDs preserved, alias marker trusted."""
    data, target = Path(data).resolve(), Path(target).expanduser().resolve()
    problems, pliegos = [], []
    if not target.is_dir():
        problems.append('El Margen destino no existe: '+str(target))
    else:
        found = _scan_vaults(target)
        for folder in sorted(target.iterdir()):
            if folder.is_symlink() or not folder.is_dir() or folder.name.startswith('.'):
                continue
            if not (folder/'learning/learning.sqlite3').is_file() or not (folder/'assets').is_dir():
                if _is_pliego(folder) or (folder/'learning').exists():
                    problems.append('Faltan datos en '+str(folder))
        for item in found.values():
            pliegos.append({'id': item['id'], 'title': item['title'], 'path': item['path'],
                            'counts': _counts(Path(item['path'])/'learning/learning.sqlite3')})
    alias = rooms.local_scope(data)
    local = None
    if alias is not None:
        local = {'id': 'local', 'path': alias['path'], 'title': alias['title']}
    elif include_local and (data/rooms.LOCAL_ALIAS_FILE).exists():
        problems.append('El marcador de la biblioteca local no se pudo verificar; se usa la carpeta original.')
    return {'target': str(target), 'pliegos': pliegos, 'local': local, 'problems': problems}


def main():
    parser = argparse.ArgumentParser(description='Planificar y aplicar la migración de pliegos a un Margen visible.')
    parser.add_argument('action', choices=['plan', 'dry-run', 'apply', 'verify'])
    parser.add_argument('--data', type=Path, default=Path(os.environ.get('LEARNING_DATA_DIR', ROOT/'.local-data')))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--target', type=Path, default=None)
    parser.add_argument('--respaldo', type=Path, default=None, help='Carpeta de respaldo fuera del repositorio (obligatoria en apply).')
    parser.add_argument('--sin-local', action='store_true', help='No migrar la biblioteca local.')
    parser.add_argument('--nombre-local', default=LOCAL_TITLE)
    parser.add_argument('--recuperar', action='store_true', help='Limpiar restos propios de una migración interrumpida y continuar.')
    args = parser.parse_args()
    include_local = not args.sin_local
    try:
        if args.action in ('plan', 'dry-run'):
            result = plan_migration(args.data, args.root, args.target, include_local, args.nombre_local)
            if args.action == 'dry-run':
                result['dryRun'] = True
            print(json.dumps({'ok': True, **result}, ensure_ascii=False, indent=2))
        elif args.action == 'apply':
            result = apply_migration(args.data, args.root, args.target, args.respaldo, include_local, args.nombre_local, args.recuperar)
            print(json.dumps({'ok': True, 'informe': str(Path(result['backup'])/REPORT_NAME), **result}, ensure_ascii=False, indent=2))
        else:
            target = args.target or (Path.home()/rooms.DEFAULT_MARGEN_NAME)
            print(json.dumps({'ok': True, **verify_migration(args.data, args.root, target, include_local)}, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, sqlite3.Error) as exc:
        parser.exit(1, 'No se completó: '+str(exc)+'\n')


if __name__ == '__main__':
    main()
