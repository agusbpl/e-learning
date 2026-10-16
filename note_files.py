"""Archivos Markdown originales de los apuntes.

La fuente de verdad de un apunte es su archivo `.md`: se puede editar dentro de
Glosa o con cualquier editor externo (Obsidian, Vim, …). SQLite guarda un índice,
las revisiones efectivas y la conversación, pero nunca pisa el archivo en
silencio.

Formato (legible y de ida y vuelta sin pérdida). El **texto** del apunte general
y el de cada página del PDF viven en el cuerpo Markdown, visibles y editables
fuera de Glosa, delimitados por comentarios HTML estables (invisibles al
renderizar). El JSON solo guarda la estructura auxiliar (anclas y study):

```
---
glosa_schema: 1
glosa_id: 3f2a…            # ID estable; sobrevive a renombres y movimientos
glosa_revision: 4
glosa_sync: <sha256>       # huella de contenido+metadata para detectar cambios
title: Derivadas
folder: Análisis/Unidad 3
shared: false
documentId: null
page: null
writingScope: general
contentFormat: markdown
createdAt: 2026-10-16T…
updatedAt: 2026-10-16T…
---

<!-- glosa:general -->
# Derivadas

Apunte general, tal cual lo escribe la persona.
<!-- /glosa:general -->

<!-- glosa:page id="doc-1" page="3" -->
Notas de la página 3 del PDF, también editables acá.
<!-- /glosa:page -->

<!-- glosa:data
{"anchors":[…],"study":{…}}
-->
```

Las claves de frontmatter que Glosa no administra se conservan tal cual al
reescribir un archivo ya existente; los archivos ajenos nunca se reescriben si
no se guardan desde Glosa.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

SCHEMA = 1
GENERAL_OPEN = '<!-- glosa:general -->'
GENERAL_CLOSE = '<!-- /glosa:general -->'
PAGE_OPEN = '<!-- glosa:page'
PAGE_CLOSE = '<!-- /glosa:page -->'
PAGE_OPEN_RE = re.compile(r'<!-- glosa:page id="([A-Za-z0-9_.\-]{1,100})" page="([1-9][0-9]{0,6})" -->')
DATA_OPEN = '<!-- glosa:data\n'
DATA_CLOSE = '-->'
DATA_MARKER = re.compile(r'\n<!-- glosa:data[ \t]*\n')
# Orden estable de las claves que Glosa administra.
FRONT_ORDER = ('glosa_schema', 'glosa_id', 'glosa_revision', 'glosa_sync',
               'title', 'folder', 'shared', 'documentId', 'page',
               'writingScope', 'contentFormat', 'createdAt', 'updatedAt')
GLOSA_KEYS = frozenset(FRONT_ORDER)
FOREIGN_KEYS = ('title',)
# Claves auxiliares guardadas en el comentario de datos (nunca el texto de páginas).
AUX_KEYS = ('anchors', 'study')
MODES = ('body', 'markdown')
WRITING_SCOPES = ('general', 'page')
_ID = re.compile(r'[A-Za-z0-9_.-]{1,100}')
_ILLEGAL = re.compile(r'[\\/:*?"<>|#^\[\]\x00-\x1f]')


class NoteFileError(ValueError):
    """Error recuperable del archivo de apunte: se informa y no se pisa nada."""


class NoteFormatError(NoteFileError):
    """El archivo existe pero no tiene el formato esperado."""


class NoteConflictError(NoteFileError):
    """El archivo cambió entre la lectura y la escritura: no se sobrescribe."""


# El archivo destino no debe existir al momento de escribir.
NO_FILE = object()


# --------------------------------------------------------------------------- #
# Nombres humanos y seguros
# --------------------------------------------------------------------------- #

def safe_segment(text, fallback='Apunte', limit=80):
    """Un solo componente de ruta: sin separadores, sin traversal, sin control."""
    value = unicodedata.normalize('NFC', str(text if text is not None else ''))
    value = _ILLEGAL.sub(' ', value)
    value = re.sub(r'\s+', ' ', value).strip()
    value = value.strip('. ').strip()
    if not value or value in ('.', '..'):
        value = fallback
    if len(value) > limit:
        value = value[:limit].rstrip(' .') or fallback
    return value


def folder_segments(folder):
    """Carpeta humana dividida en segmentos seguros; descarta vacíos y `..`."""
    segments = []
    for part in re.split(r'[\\/]+', str(folder if folder is not None else '')):
        part = part.strip()
        if part in ('', '.', '..'):
            continue
        segments.append(safe_segment(part, 'Carpeta', 60))
    return segments


def relative_note_path(folder, title):
    """Ruta relativa POSIX dentro de la raíz de apuntes."""
    return '/'.join([*folder_segments(folder), safe_segment(title, 'Apunte', 80) + '.md'])


def folder_from_path(relative):
    """Carpeta humana derivada de la ubicación del archivo."""
    parts = [p for p in str(relative).split('/')[:-1] if p not in ('', '.', '..')]
    return '/'.join(parts)


_TITLE_HEADING = re.compile(r'^\s{0,3}#\s+(.+?)\s*#*\s*$')


def title_from_text(text, fallback='Apunte'):
    for line in str(text).splitlines():
        match = _TITLE_HEADING.match(line)
        if match:
            return match.group(1).strip()[:200] or fallback
        if line.strip():
            break
    return fallback


# --------------------------------------------------------------------------- #
# Escalares de frontmatter
# --------------------------------------------------------------------------- #

def _scalar(value):
    if value is None:
        return 'null'
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    if isinstance(value, int):
        return str(value)
    text = str(value)
    plain = (text != '' and text.strip() == text
             and not re.search(r'[\n\r:#]', text)
             and text not in ('null', '~', 'true', 'false')
             and not re.fullmatch(r'-?\d+', text)
             and text[0] not in '[]{}"\'*&!?|>%@`')
    return text if plain else json.dumps(text, ensure_ascii=False)


def _parse_scalar(raw):
    text = raw.strip()
    if text in ('', 'null', '~'):
        return None
    if text == 'true':
        return True
    if text == 'false':
        return False
    if re.fullmatch(r'-?\d+', text):
        return int(text)
    if text[:1] == '"':
        try:
            return json.loads(text)
        except ValueError:
            return raw
    if text[:1] == "'" and text[-1:] == "'" and len(text) >= 2:
        return text[1:-1].replace("''", "'")
    return raw


def _line_key(line):
    match = re.match(r'^([A-Za-z0-9_.-]+):', line)
    return match.group(1) if match else None


def _parse_front(head):
    """Devuelve (values, lines): valores de `clave: valor` y líneas crudas."""
    values, lines = {}, []
    for line in head.split('\n'):
        line = line.rstrip('\r')
        if not line.strip():
            continue
        lines.append(line)
        if line.lstrip().startswith('#'):
            continue
        match = re.match(r'^([A-Za-z0-9_.-]+):[ \t]?(.*)$', line)
        if match:
            values[match.group(1)] = _parse_scalar(match.group(2))
    return values, lines


# --------------------------------------------------------------------------- #
# Cuerpo: secciones visibles general y por página
# --------------------------------------------------------------------------- #

def _extract_general(body, first_page):
    start = body.find(GENERAL_OPEN)
    if start == -1:
        end = first_page if first_page != -1 else len(body)
        return body[:end].rstrip('\n'), end
    start += len(GENERAL_OPEN)
    if body[start:start + 1] == '\n':
        start += 1
    close = body.find(GENERAL_CLOSE, start)
    if close == -1:
        raise NoteFormatError('La sección general del apunte no cierra con '+GENERAL_CLOSE+'.')
    text = body[start:close]
    if text.endswith('\n'):
        text = text[:-1]
    return text, close + len(GENERAL_CLOSE)


def _extract_pages(body, start):
    pages = {}
    order = []
    pos = start
    while True:
        match = PAGE_OPEN_RE.search(body, pos)
        if not match:
            break
        page_start = match.end()
        if body[page_start:page_start + 1] == '\n':
            page_start += 1
        close = body.find(PAGE_CLOSE, page_start)
        if close == -1:
            raise NoteFormatError('Una página del apunte no cierra con '+PAGE_CLOSE+'.')
        key = (match.group(1), int(match.group(2)))
        if key in pages:
            raise NoteFormatError('La página '+str(key[1])+' de la fuente '+key[0]+' está repetida.')
        text = body[page_start:close]
        if text.endswith('\n'):
            text = text[:-1]
        pages[key] = text
        order.append(key)
        pos = close + len(PAGE_CLOSE)
    return pages, order


def _render_sections(content, page_notes):
    parts = [GENERAL_OPEN, '\n', content, '\n', GENERAL_CLOSE]
    for source in sorted(page_notes):
        group = page_notes[source]
        if not isinstance(group, dict):
            continue
        for page in sorted(group, key=lambda value: int(value)):
            parts += ['\n\n', '<!-- glosa:page id="'+source+'" page="'+str(int(page))+'" -->', '\n', group[page], '\n', PAGE_CLOSE]
    return ''.join(parts)


# --------------------------------------------------------------------------- #
# Lectura y escritura
# --------------------------------------------------------------------------- #

def parse_note_file(text):
    """Separa frontmatter, cuerpo, páginas y datos auxiliares.

    El cuerpo NO se normaliza: se conserva exactamente lo que está entre los
    delimitadores para no alterar el texto de la persona.
    """
    if text.startswith('\ufeff'):
        text = text[1:]
    # Un editor de Windows puede guardar CRLF: normalizamos saltos para leer el
    # contenido sin alterar lo que ve la persona.
    if '\r' in text:
        text = text.replace('\r\n', '\n').replace('\r', '\n')
    result = {'front': {}, 'front_lines': [], 'content': text, 'pageNotes': {},
              'extras': {}, 'data_present': False, 'had_frontmatter': False}
    opening = re.match(r'^---[ \t]*\r?\n', text)
    if not opening:
        return result
    closing = re.search(r'\r?\n---[ \t]*\r?\n', text[opening.end():])
    if not closing:
        raise NoteFormatError('El frontmatter del apunte no está cerrado con ---.')
    head = text[opening.end(): opening.end() + closing.start()]
    rest = text[opening.end() + closing.end():]
    result['had_frontmatter'] = True
    result['front'], result['front_lines'] = _parse_front(head)

    body = rest
    # Comentario de datos auxiliares al final (sin el texto de páginas).
    matches = list(DATA_MARKER.finditer(body))
    if matches:
        marker = matches[-1]
        tail = body[marker.end():]
        end = tail.rfind(DATA_CLOSE)
        if end != -1 and tail[end + len(DATA_CLOSE):].strip() == '':
            candidate = tail[:end].strip()
            try:
                parsed = json.loads(candidate)
            except ValueError:
                parsed = None
            if isinstance(parsed, dict):
                result['extras'] = parsed
                result['data_present'] = True
                body = body[:marker.start()]

    first_page = PAGE_OPEN_RE.search(body)
    content, cursor = _extract_general(body, first_page.start() if first_page else -1)
    pages, _order = _extract_pages(body, cursor)
    if pages:
        result['pageNotes'] = {}
        for (source, page), value in pages.items():
            result['pageNotes'].setdefault(source, {})[str(page)] = value
    elif isinstance(result['extras'].get('pageNotes'), dict):
        # Compatibilidad con el primer borrador (texto de páginas en JSON).
        result['pageNotes'] = result['extras']['pageNotes']
    result['content'] = content
    return result


def is_glosa_id(value):
    return isinstance(value, str) and bool(_ID.fullmatch(value)) and value not in ('.', '..')


def _recognized_front(parsed):
    glosa_id = parsed['front'].get('glosa_id')
    keys = GLOSA_KEYS if is_glosa_id(glosa_id) else FOREIGN_KEYS
    return {key: parsed['front'][key] for key in keys if key in parsed['front']}


def note_sync(meta, content, page_notes, extras):
    """Huella estable de lo que define el contenido del apunte (sin revisión)."""
    payload = {
        'title': meta.get('title') or '',
        'folder': meta.get('folder') or '',
        'shared': bool(meta.get('shared')),
        'documentId': meta.get('documentId'),
        'page': meta.get('page'),
        'writingScope': meta.get('writingScope') or 'general',
        'contentFormat': meta.get('contentFormat') or 'body',
        'content': content,
        'pageNotes': page_notes,
        'aux': {key: extras[key] for key in AUX_KEYS if key in extras},
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(blob).hexdigest()


def read_note_file(path):
    """Lee un archivo de apunte. Lanza NoteFileError si no se puede leer."""
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise NoteFileError('No se pudo leer el apunte: '+str(exc)) from None
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise NoteFormatError('El apunte no está en UTF-8. Guardalo en UTF-8 para incorporarlo.') from None
    parsed = parse_note_file(text)
    glosa_id = parsed['front'].get('glosa_id')
    revision = parsed['front'].get('glosa_revision')
    stored = parsed['front'].get('glosa_sync')
    meta = _recognized_front(parsed)
    extras = {key: parsed['extras'][key] for key in AUX_KEYS if key in parsed['extras']}
    return {
        'glosa_id': glosa_id if is_glosa_id(glosa_id) else None,
        'revision': revision if isinstance(revision, int) and not isinstance(revision, bool) else None,
        'stored_sync': stored if isinstance(stored, str) else None,
        'sync': note_sync(meta, parsed['content'], parsed['pageNotes'], extras),
        'meta': meta,
        'content': parsed['content'],
        'pageNotes': parsed['pageNotes'],
        'extras': extras,
        'front': parsed['front'],
        'front_lines': parsed['front_lines'],
        'data_present': parsed['data_present'],
        'had_frontmatter': parsed['had_frontmatter'],
    }


def render_note_file(note, base=None):
    """Escribe el apunte en Markdown. Devuelve (texto, huella sync)."""
    base = base or {}
    managed = {
        'glosa_schema': SCHEMA,
        'glosa_id': note['id'],
        'glosa_revision': note.get('revision') or 1,
        'title': note.get('title') or 'Apunte',
        'folder': note.get('folder') or '',
        'shared': bool(note.get('shared')),
        'documentId': note.get('documentId'),
        'page': note.get('page'),
        'writingScope': note.get('writingScope') or 'general',
        'contentFormat': note.get('contentFormat') if note.get('contentFormat') in MODES else 'body',
        'createdAt': note.get('createdAt') or '',
        'updatedAt': note.get('updatedAt') or '',
    }
    content = note.get('content') or ''
    page_notes = note.get('pageNotes') if isinstance(note.get('pageNotes'), dict) else {}
    page_notes = {source: {str(page): text for page, text in group.items()}
                  for source, group in page_notes.items() if isinstance(group, dict)}
    extras = {key: base.get('extras')[key] for key in AUX_KEYS
              if isinstance(base.get('extras'), dict) and key in base['extras']}
    if note.get('anchors'):
        extras['anchors'] = note['anchors']
    else:
        extras.pop('anchors', None)
    if note.get('study'):
        extras['study'] = note['study']
    else:
        extras.pop('study', None)
    meta = {key: managed[key] for key in ('title', 'folder', 'shared', 'documentId',
                                          'page', 'writingScope', 'contentFormat')}
    sync = note_sync(meta, content, page_notes, extras)
    managed['glosa_sync'] = sync
    lines = [key+': '+_scalar(managed[key]) for key in FRONT_ORDER]
    # Claves ajenas que no administramos se conservan tal cual.
    lines.extend(line for line in base.get('front_lines', []) if _line_key(line) not in GLOSA_KEYS)
    text = '---\n' + '\n'.join(lines) + '\n---\n\n' + _render_sections(content, page_notes)
    if extras:
        text += '\n\n' + DATA_OPEN + json.dumps(extras, ensure_ascii=False, sort_keys=False) + '\n' + DATA_CLOSE + '\n'
    else:
        text += '\n'
    return text, sync


def write_atomic(path, text, root=None, expect=None):
    """Escritura atómica con guarda optimista y sin seguir symlinks.

    `expect` permite un compare-and-swap aproximado contra el bytes que se leyó
    al planificar: si el archivo cambió desde entonces, se aborta sin tocar
    nada (evita pisar una edición externa en la ventana entre lectura y
    reemplazo). No es un CAS perfecto con editores arbitrarios, pero preserva
    los bytes desplazados.
    """
    path = Path(path)
    if root is not None:
        root = Path(root).resolve()
        if path.is_symlink() or not _inside(path, root):
            raise NoteFileError('Ruta de apunte fuera de la carpeta de apuntes.')
    if expect is not None:
        exists = path.is_file() and not path.is_symlink()
        if expect is NO_FILE:
            if exists:
                raise NoteConflictError('El archivo apareció mientras se guardaba.')
        else:
            current = path.read_bytes() if exists else None
            if current != expect:
                raise NoteConflictError('El archivo cambió mientras se guardaba.')
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    for parent in path.parents:
        if not parent.exists():
            continue
        if parent.is_symlink():
            raise NoteFileError('La carpeta del apunte contiene un enlace simbólico.')
    temporary = path.with_name('.'+path.name+'.'+os.urandom(6).hex()+'.tmp')
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def _inside(path, root):
    try:
        resolved = Path(os.path.realpath(path))
        return resolved == root or root in resolved.parents
    except OSError:
        return False
