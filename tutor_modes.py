"""Modos del tutor y plan global de parciales del Margen: política local y determinista.

Sin llamadas a proveedores ni azar: toda decisión se explica con motivos medibles
y fechas reales. No fabrica fechas, temarios, horarios ni prioridades; las
incertidumbres se declaran. Recibe `server` y abre scopes seguros con las APIs
existentes (rooms.margen, rooms.room, server.ACTIVE_WORKSPACE, server.connect,
server.snapshot): no inventa endpoints ni migraciones.

Alcance: TODO el Margen seleccionado (todos los pliegos, sin el tutorial
'primer-trazo'). Cada pliego conserva su base y sus IDs; los targets son
compuestos roomId|courseId|eventId|lessonId para evitar colisiones. Apuntes con
`study.parcialDate` entran como fecha declarada por el alumno (nunca inventada).

Persistencia: un único archivo por Margen canónico (`server.DATA/tutor-modes/
margen-<sha1>.json`) con preferencia, último modo efectivo, aviso pendiente,
temarios por parcial y ediciones del plan. Contrato de payload para respaldo en
`export_payload`/`import_payload` y en modes-integration.md.

Ver docs/modos-tutor.md.
"""
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path

import calendar_store

POLICY_VERSION = 'tutorModes-1'
FORMAT = 'glosa-tutor-modes'
MODES = ('flexible', 'strict', 'extreme')
MODE_LABELS = {'flexible': 'Flexible', 'strict': 'Estricto', 'extreme': 'Extremo'}
URGENT_DAYS = 7
URGENT_READINESS = 0.5
SOON_DAYS = 21
GATE_CLAUSE = ('Adaptar la modalidad no debilita la puerta de evidencia: sin aplicación nueva '
               'tras una ayuda y sin evidencia propia por criterio, el estado queda pending o '
               'with_help y jamás independent simulado.')

MODE_CONTRACT = {
    'flexible': {
        'meaning': 'Avanzar tras una comprobación breve, conservando lo pendiente; sin falsear dominio.',
        'instructions': ('Modo Flexible. Evaluá contra la rúbrica con evidencia real. Una comprobación '
                         'breve y correcta habilita avanzar a lo siguiente, pero conservá pendientes, '
                         'ayudas recibidas y criterios no logrados tal como están. No declares dominio '
                         'que el estudiante no acreditó: una ayuda previa exige luego una aplicación '
                         'nueva para independencia. Incertidumbre queda pending. Avisá qué quedó '
                         'pendiente y por qué se avanza. Una pregunta focalizada por intervención; tras '
                         'dos intentos sin progreso, explicá y comprobá con un caso nuevo.'),
        'requirements': ['comprobación breve con evidencia textual del estudiante',
                         'pendientes, ayudas y criterios no logrados quedan conservados',
                         'avanzar por falta de tiempo no acredita aprendizaje'],
        'never': ['marcar independent inventado', 'ocultar pendientes', 'debilitar la puerta de evidencia'],
    },
    'strict': {
        'meaning': 'Determinar comprensión con evidencia real contra la rúbrica.',
        'instructions': ('Modo Estricto. Comprobá la comprensión con evidencia real: cita breve literal '
                         'del estudiante por criterio y met/partial/not_met/uncertain. Respuestas breves '
                         'y paráfrasis valen cuando cubren el criterio; longitud, estilo y seguridad no '
                         'son evidencia. Elegir bien, adivinar o repetir lo revelado no comprueba dominio '
                         'independiente. Tras dos intentos sin progreso, explicá brevemente con analogía '
                         'limitada o contraejemplo válido y comprobá transferencia con un caso distinto. '
                         'No transfieras lo dominado de un criterio a los demás.'),
        'requirements': ['evidencia real por criterio según la rúbrica',
                         'independencia exige aplicación nueva sin ayuda previa',
                         'incertidumbre declarada como uncertain/pending'],
        'never': ['acreditar dominio por estilo o coincidencia literal', 'debilita la puerta de evidencia'],
    },
    'extreme': {
        'meaning': 'Dominio real: transferencia nueva, contraejemplos y defensa ante objeciones.',
        'instructions': ('Modo Extremo. Exigí dominio real sin hostilidad: transferencia a casos nuevos '
                         'no trabajados, contraejemplos donde el tema lo permita y defensa ante '
                         'objeciones plausibles, con la exigencia ADAPTADA AL TEMA (no una checklist '
                         'rígida de todas las técnicas en cada concepto). Explicitá qué evidencia '
                         'falta. Juzgá razonamiento según la rúbrica: longitud, estilo, confianza y '
                         'acuerdo con vos no son evidencia. Tras dos intentos sin progreso, explicá '
                         'con analogía limitada o contraejemplo válido y comprobá transferencia con un '
                         'caso nuevo distinto del que falló.'),
        'requirements': ['transferencia a un caso nuevo del tema',
                         'contraejemplo o defensa ante objeciones donde el tema lo permita',
                         'explicitar qué evidencia falta',
                         'criterio adaptado al tema, sin checklist rígida universal'],
        'never': ['hostilidad o castigo', 'pesar por longitud o estilo', 'debilitar la puerta de evidencia'],
    },
}


def mode_requirements(mode):
    """Requisitos canónicos del modo para adjuntar a cada respuesta de API y MCP."""
    if mode not in MODES:
        raise ValueError('Modo desconocido: debe ser flexible, strict o extreme.')
    contract = MODE_CONTRACT[mode]
    return {'mode': mode, 'label': MODE_LABELS[mode], 'version': POLICY_VERSION,
            'meaning': contract['meaning'], 'evidenceRequirements': contract['requirements'],
            'never': contract['never'] + [GATE_CLAUSE]}


def mode_prompt(mode):
    """Instrucciones que deben preceder a la generación del tutor (API y MCP), no solo metadatos."""
    if mode not in MODES:
        raise ValueError('Modo desconocido: debe ser flexible, strict o extreme.')
    return MODE_CONTRACT[mode]['instructions']


def normalize_preference(raw, today=None):
    """Valida y canoniza la preferencia; sin valores inventados."""
    if not isinstance(raw, dict) or raw.get('choice') not in ('manual', 'auto'):
        raise ValueError('La preferencia del tutor debe ser manual o auto.')
    mode = raw.get('mode')
    if raw['choice'] == 'manual' and mode not in MODES:
        raise ValueError('El modo manual debe ser flexible, strict o extreme.')
    if raw['choice'] == 'auto' and mode not in (None, ''):
        raise ValueError('Con auto no se elige modo: lo decide la política local.')
    updated = raw.get('updatedAt') or today or date.today().isoformat()
    return {'choice': raw['choice'], 'mode': mode if raw['choice'] == 'manual' else None, 'updatedAt': updated}


# ------------------------------------------------------------------ scopes

def _rooms():
    import rooms
    return rooms


def _margen_identity(server):
    """Identidad canónica del Margen elegido: la preferencia no se comparte entre Margens."""
    try:
        return str(Path(_rooms().margen(server.DATA, create=False)['path']).resolve())
    except (ValueError, OSError, KeyError, TypeError):
        return str(Path(server.DATA).resolve())


def scopes(server):
    """Pliegos del Margen con la API existente; sin el tutorial y sin duplicados."""
    rooms = _rooms()
    out, seen = [], set()
    try:
        listing = rooms.list_rooms(server.DATA, server.ROOT)
    except Exception:
        listing = []
    for item in listing:
        rid = item['id']
        if rid == rooms.TUTORIAL_ID or rid in seen:
            continue
        try:
            scope = rooms.room(server.DATA, server.ROOT, rid)
        except Exception:
            continue
        if not isinstance(scope, dict):
            continue
        seen.add(rid)
        out.append({'scope': scope, 'id': rid, 'title': scope.get('title') or item.get('title', rid)})
    return out


class _Scoped:
    """Fija el contextvar del scope con la API existente; al salir la restaura."""

    def __init__(self, server, scope):
        self.server, self.token = server, None
        self.scope = scope

    def __enter__(self):
        self.token = self.server.ACTIVE_WORKSPACE.set(self.scope)
        return self

    def __exit__(self, *exc):
        self.server.ACTIVE_WORKSPACE.reset(self.token)
        return False


# ------------------------------------------------------------------ persistencia global

def store_path(server):
    identity = _margen_identity(server)
    digest = hashlib.sha1(identity.encode('utf-8')).hexdigest()[:16]
    return Path(server.DATA) / 'tutor-modes' / ('margen-' + digest + '.json')


def _empty_state():
    return {'format': FORMAT, 'policyVersion': POLICY_VERSION, 'margenPath': '', 'preference':
            {'choice': 'auto', 'mode': None, 'updatedAt': None}, 'lastEffectiveMode': None,
            'notice': None, 'examTopics': {}, 'planEdits': []}


def read_state(server):
    path = store_path(server)
    state = _empty_state()
    if not path.exists():
        return state
    try:
        stored = json.loads(path.read_text())
    except (ValueError, OSError):
        return state
    if not isinstance(stored, dict) or stored.get('format') != FORMAT:
        return state
    for key in ('preference', 'examTopics', 'planEdits', 'lastEffectiveMode', 'notice'):
        if key in stored:
            state[key] = stored[key]
    return state


def write_state(server, state):
    path = store_path(server)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {**_empty_state(), **state, 'format': FORMAT, 'policyVersion': POLICY_VERSION,
             'margenPath': _margen_identity(server)}
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    os.replace(temporary, path)
    return state


def export_payload(server):
    """Payload exacto para respaldo/restauración del integrador (sin inventar datos)."""
    return {**_empty_state(), **read_state(server), 'format': FORMAT,
            'policyVersion': POLICY_VERSION, 'margenPath': _margen_identity(server)}


def import_payload(server, payload):
    if not isinstance(payload, dict) or payload.get('format') != FORMAT:
        raise ValueError('Payload de modos inválido.')
    return write_state(server, {key: payload[key] for key in
                                ('preference', 'examTopics', 'planEdits', 'lastEffectiveMode', 'notice') if key in payload})


def read_preference(server):
    """Preferencia manual/auto del Margen elegido."""
    state = read_state(server)
    preference = state.get('preference')
    if not isinstance(preference, dict) or preference.get('choice') not in ('manual', 'auto'):
        return {'source': 'default', 'choice': 'auto', 'mode': None, 'updatedAt': None}
    return {'source': 'margen', **preference}


def save_preference(server, preference):
    preference = normalize_preference(preference)
    state = read_state(server)
    state['preference'] = preference
    write_state(server, state)
    return {'source': 'margen', **preference}


def read_exam_topics(server, room_id=None):
    """Temarios por parcial con targets compuestos; validados contra cada pliego."""
    topics = read_state(server).get('examTopics', {})
    if not isinstance(topics, dict):
        return {}
    if room_id:
        return {key: value for key, value in topics.items() if key.split('|')[0] == room_id}
    return topics


def save_exam_topics(server, room_id, course_id, event_id, lesson_ids, note_ids=(), status='proposed',
                     proposed_by='author-mcp', confirmed_by='', source_note='', expected_revision=0):
    """Propuesta/confirmación de temario con evidencia real; sin fechas ni alcance inventados."""
    rooms_mod = _rooms()
    scope = rooms_mod.room(server.DATA, server.ROOT, room_id)
    with _Scoped(server, scope):
        state = server.snapshot()
    course = next((c for c in state['courses'] if c['id'] == course_id), None)
    if course is None:
        raise ValueError('Curso inexistente en el pliego indicado.')
    known_lessons = {l['id'] for l in course['lessons']}
    lesson_ids = list(lesson_ids) if isinstance(lesson_ids, (list, tuple)) else []
    if not lesson_ids:
        raise ValueError('El temario necesita lessonIds reales; no se inventa alcance.')
    unknown = [i for i in lesson_ids if i not in known_lessons]
    if unknown:
        raise ValueError('Lecciones inexistentes en el curso: ' + ', '.join(unknown))
    note_ids = list(note_ids) if isinstance(note_ids, (list, tuple)) else []
    known_notes = {n['id'] for n in state.get('library', {}).get('notes', [])}
    unknown_notes = [i for i in note_ids if i not in known_notes]
    if unknown_notes:
        raise ValueError('Apuntes inexistentes: ' + ', '.join(unknown_notes))
    key = '|'.join((room_id, course_id, event_id))
    topics = read_state(server).get('examTopics', {})
    current = topics.get(key, {})
    if current.get('revision', 0) != expected_revision:
        raise ValueError('El temario cambió. Recargá antes de editar.')
    entry = {'courseId': course_id, 'lessonIds': lesson_ids, 'noteIds': note_ids,
             'status': 'confirmed' if status == 'confirmed' else 'proposed',
             'proposedBy': str(proposed_by), 'confirmedBy': str(confirmed_by),
             'sourceNote': str(source_note), 'revision': expected_revision + 1}
    state = read_state(server)
    state.setdefault('examTopics', {})[key] = entry
    write_state(server, state)
    return {'roomId': room_id, 'courseId': course_id, 'eventId': event_id, **entry}


def read_plan_edits(server):
    edits = read_state(server).get('planEdits', [])
    return list(edits) if isinstance(edits, list) else []


def save_plan_edits(server, edits):
    """Orden y prioridad elegidos por el alumno; la asignación real de minutos lo respeta."""
    if not isinstance(edits, list) or not edits or not all(isinstance(item, str) for item in edits):
        raise ValueError('Ediciones inválidas: se esperaban targets roomId|courseId|eventId.')
    state = read_state(server)
    state['planEdits'] = edits
    write_state(server, state)
    return edits


# ------------------------------------------------------------------ señales

def course_status(course, events):
    """Estado por lección de la versión vigente, sin heredar dominio de versiones previas."""
    evidence = {}
    cancelled = {rid for ev in events if ev.get('courseId') == course['id'] and ev['kind'] == 'self_review_cancel'
                 and ev['data'].get('courseVersion', course['version']) == course['version'] and isinstance(ev['data'].get('reviewIds'), list)
                 for rid in ev['data']['reviewIds'] if isinstance(rid, str)}
    for ev in events:
        if ev.get('courseId') != course['id'] or ev['data'].get('courseVersion', course['version']) != course['version']:
            continue
        if ev['kind'] == 'assessment':
            evidence[ev['lessonId']] = ev['data'].get('status', 'pending')
        elif ev['kind'] == 'self_review' and ev['id'] not in cancelled and evidence.get(ev['lessonId']) != 'independent':
            evidence[ev['lessonId']] = 'self_review'
    return evidence


def lesson_difficulty(course, lesson_id, statuses, events):
    """Dificultad por evidencia: intentos, respuestas con ayuda, incertidumbre; autorreporte aparte."""
    attempts = helped = 0
    for ev in events:
        if ev.get('courseId') != course['id'] or ev.get('lessonId') != lesson_id:
            continue
        if ev['kind'] == 'assessment' and ev['data'].get('courseVersion', course['version']) == course['version']:
            attempts += 1
        elif ev['kind'] == 'answer' and ev['data'].get('courseVersion', course['version']) == course['version'] and ev['data'].get('helpReceived'):
            helped += 1
    status = statuses.get(lesson_id, 'unseen')
    level = (1 if helped else 0) + (1 if attempts >= 3 else 0) + (1 if status == 'uncertain' else 0)
    return {'attempts': attempts, 'helped': helped, 'level': min(level, 3),
            'selfReport': None, 'status': status}


def note_difficulty(notes, materia):
    """Señal declarada por el alumno en apuntes (errores/necesidad de práctica); nunca evidencia de dominio."""
    materia = (materia or '').strip().lower()
    errors = practice = 0
    for note in notes or []:
        study = note.get('study') if isinstance(note, dict) else None
        if not isinstance(study, dict):
            continue
        if materia and (study.get('materia') or '').strip().lower() != materia:
            continue
        errors += len(study.get('errors', [])) if isinstance(study.get('errors'), list) else 0
        practice += 1 if study.get('needsPractice') is True else 0
    return {'declaredErrors': errors, 'needsPractice': practice}


# ------------------------------------------------------------------ temario / plan

def temario_of(course, topics):
    """Temario por parcial: confirmado > propuesto > materia completa; siempre declara la fuente."""
    lesson_ids = [l['id'] for l in course['lessons']]
    if isinstance(topics, dict) and topics.get('lessonIds'):
        known = [i for i in topics['lessonIds'] if i in lesson_ids]
        unknown = [i for i in topics['lessonIds'] if i not in lesson_ids]
        if topics.get('status') == 'confirmed':
            notes = [] if not unknown else ['El temario confirmado cita lecciones inexistentes; se omiten: ' + ', '.join(unknown)]
            return {'source': 'confirmed', 'lessonIds': known, 'uncertain': notes}
        return {'source': 'proposed', 'lessonIds': known or lesson_ids,
                'uncertain': ['Temario propuesto y sin confirmar' + ('; lecciones inexistentes omitidas: ' + ', '.join(unknown) if unknown else '')]}
    return {'source': 'full_course', 'lessonIds': lesson_ids,
            'uncertain': ['Sin temario confirmado para este compromiso: se considera la materia completa.']}


def readiness(temario, statuses):
    mastered = sum(1 for i in temario['lessonIds'] if statuses.get(i) == 'independent')
    total = len(temario['lessonIds'])
    return {'mastered': mastered, 'total': total, 'ratio': (mastered / total) if total else 0.0, 'source': temario['source']}


def pending_lessons(course, temario, statuses):
    by_id = {l['id']: l for l in course['lessons']}
    pendings = [by_id[i] for i in temario['lessonIds'] if i in by_id and statuses.get(i) != 'independent']
    return sorted(pendings, key=lambda l: (l.get('priority', 3), -int(l.get('minutes', 0) or 0)))


def day_minutes(settings, day):
    """Minutos declarados para un día; override y fin de semana; sin doble conteo."""
    overrides = settings.get('dailyOverrides') if isinstance(settings.get('dailyOverrides'), dict) else {}
    default = settings.get('weekdayMinutes', 0) if day.weekday() < 5 else settings.get('weekendMinutes', 0)
    value = overrides.get(day.isoformat(), default)
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 0
    return max(0, value)


def _days_between(start, end):
    cursor = start
    while cursor <= end:
        yield cursor
        cursor += timedelta(days=1)


def _entry_score(entry):
    """Puntaje determinista y explicable: proximidad + brecha + dificultad propia + presión + tipo."""
    reasons = []
    days = entry.get('daysLeft')
    if days is None:
        return 0.0, ['Sin fecha confiable: sin puntaje inventado.']
    capped = max(0, min(90, days))
    score = (90 - capped) * 100 / 90
    reasons.append('Proximidad: %d día(s) (aporta %.1f)' % (days, score))
    gap = entry['temarioReadiness']
    if gap['total'] and gap['mastered'] < gap['total']:
        contribution = max(0, 1 - gap['ratio']) * 40
        score += contribution
        reasons.append('Sin dominio acreditado: %d/%d temas pendientes (aporta %.1f)' % (gap['total'] - gap['mastered'], gap['total'], contribution))
    difficulty = entry['difficulty']
    if difficulty['level']:
        score += difficulty['level'] * 8
        reasons.append('Dificultad por evidencia nivel %d (aporta %d)' % (difficulty['level'], difficulty['level'] * 8))
    if difficulty.get('declaredErrors'):
        score += min(20, difficulty['declaredErrors'] * 2)
        reasons.append('Errores declarados en apuntes: %d (aporta %d)' % (difficulty['declaredErrors'], min(20, difficulty['declaredErrors'] * 2)))
    if difficulty.get('needsPractice'):
        score += 5
        reasons.append('El alumno marcó que necesita practicar (aporta 5)')
    if entry.get('kind') == 'exam':
        score += 15
        reasons.append('Es parcial/examen (aporta 15)')
    if entry.get('minutesDeficit', 0) > 0 and entry.get('minutesWindow') is not None and entry.get('minutesAllocated') is None:
        score += 25
        reasons.append('El tiempo declarado no alcanza para el temario pendiente (aporta 25)')
    return round(score, 1), reasons


def _priority_order(entries, edits):
    """Orden real de trabajo: edición del alumno primero (en su orden), después ranking automático."""
    ranked = sorted(entries, key=lambda e: (-e['priorityScore'], e.get('daysLeft') if e.get('daysLeft') is not None else 10 ** 6, e['target']))
    edited = [t for t in edits if any(e['target'] == t for e in entries)]
    ordered = [next(e for e in entries if e['target'] == t) for t in edited]
    ordered += [e for e in ranked if e['target'] not in set(edited)]
    return ordered


def _allocate(entries, per_day, today, edits):
    """Asigna minutos reales por prioridad, respetando la ventana de cada deadline y un pool diario único."""
    declared = any(minutes > 0 for minutes in per_day.values())
    order = _priority_order(entries, edits)
    capacity = dict(per_day)
    for position, entry in enumerate(order):
        entry['allocationRank'] = position + 1
        deadline = date.fromisoformat(entry['date']) if entry['daysLeft'] is not None else None
        days = list(_days_between(today, deadline)) if deadline else []
        entry['minutesAvailable'] = sum(capacity.get(day.isoformat(), 0) for day in days)
        for lesson in entry['pendingLessons']:
            lesson['assignedMinutes'] = 0
            need = lesson['minutes']
            if need <= 0:
                continue
            for day in days:
                if lesson['assignedMinutes'] >= need:
                    break
                key = day.isoformat()
                free = capacity.get(key, 0)
                if free <= 0:
                    continue
                take = min(free, need - lesson['assignedMinutes'])
                capacity[key] = free - take
                lesson['assignedMinutes'] += take
        allocated = sum(lesson['assignedMinutes'] for lesson in entry['pendingLessons'])
        required = entry['minutesRequired']
        entry['minutesAllocated'] = allocated
        entry['minutesDeficit'] = max(0, required - allocated)
        cover = [lesson for lesson in entry['pendingLessons'] if lesson['assignedMinutes'] >= lesson['minutes'] and lesson['minutes'] > 0]
        postponed = [lesson for lesson in entry['pendingLessons'] if lesson not in cover]
        emergency = bool(declared and entry['minutesDeficit'] > 0)
        entry['plan'] = {'cover': cover, 'postponed': postponed, 'emergency': emergency, 'declaredMinutes': declared,
                         'note': ('Plan de emergencia: el tiempo declarado no alcanza para el temario pendiente; '
                                  'queda explícito lo postergado. Avanzar sin evidencia no declara dominio. '
                                  'Podés cambiar el orden y la asignación se recalcula.' if emergency else None)}
        if not declared:
            entry['uncertainty'].append('No hay minutos declarados: no se puede afirmar urgencia de tiempo.')
        elif emergency:
            entry['uncertainty'].append('Faltan %d min declarados para el temario pendiente.' % entry['minutesDeficit'])
    return order


def plan_from_states(states, today=None, topics=None, edits=None):
    """Plan global determinista con asignación real de minutos y targets compuestos."""
    topics = topics or {}
    edits = list(edits or [])
    today = date.fromisoformat(today) if isinstance(today, str) else (today or date.today())
    entries, room_titles, notes, undated = [], {}, [], []
    for state in states:
        room_id = state['roomId']
        room_titles[room_id] = state['roomTitle']
        declared_notes = state.get('notes', [])
        for course in state['courses']:
            statuses = course_status(course, state['events'])
            difficulty_by_lesson = {l['id']: lesson_difficulty(course, l['id'], statuses, state['events']) for l in course['lessons']}
            for event in calendar_store.commitments(state['calendarEvents']):
                if event.get('courseId') != course['id']:
                    continue
                entries.append(_make_entry(room_id, state, course, event, statuses, difficulty_by_lesson, topics, declared_notes, today))
        # Apuntes: fecha de parcial declarada por el alumno (o 'sin fecha', nunca inventada).
        dated_notes = {item['noteId'] for item in calendar_store.study_dates(declared_notes)}
        for note in declared_notes:
            study = note.get('study') if isinstance(note, dict) else None
            if not isinstance(study, dict) or not study.get('materia'):
                continue
            note_id = note.get('id')
            if note_id in [e.get('noteId') for e in entries if e.get('noteId')]:
                continue
            if note_id in dated_notes:
                entries.append(_make_note_entry(room_id, state, note, study, declared_notes, today))
            else:
                undated.append({'target': '|'.join((room_id, 'note', str(note_id))), 'roomId': room_id, 'roomTitle': state['roomTitle'],
                                'noteId': note_id, 'title': note.get('title', study.get('materia')), 'materia': study.get('materia'),
                                'uncertainty': ['Sin fecha de parcial declarada en el apunte; se gestiona con el MCP de autoría.']})
    # Disponibilidad global: UNA sola cuenta por día de todo el Margen; menor si los pliegos difieren.
    per_day, conflicts = {}, set()
    dated = [entry for entry in entries if entry['daysLeft'] is not None]
    sources = []
    for state in states:
        settings = state['settings']
        sources.append('%s: %s/%s min' % (state['roomId'], settings.get('weekdayMinutes', 0), settings.get('weekendMinutes', 0)))
        for entry in dated:
            if entry['roomId'] != state['roomId']:
                continue
            cursor = today
            while cursor <= date.fromisoformat(entry['date']):
                minutes = day_minutes(settings, cursor)
                key = cursor.isoformat()
                if key in per_day and per_day[key] != minutes:
                    conflicts.add(key)
                    minutes = min(per_day[key], minutes)
                per_day[key] = minutes
                cursor += timedelta(days=1)
    if conflicts:
        notes.append('Disponibilidad declarada difiere entre pliegos (' + ', '.join(sorted(conflicts)) + '); se usa la menor. Fuentes: ' + '; '.join(sources) + '.')
    if per_day and not any(minutes > 0 for minutes in per_day.values()):
        notes.append('No hay minutos disponibles declarados; no se asignan horarios ni prioridades por invento.')
    for entry in dated:
        window = sum(per_day.get(day.isoformat(), 0) for day in _days_between(today, date.fromisoformat(entry['date'])))
        entry['minutesWindow'] = window
        entry['minutesDeficit'] = max(0, entry['minutesRequired'] - window)
        entry['priorityScore'], entry['priorityReasons'] = _entry_score(entry)
    order = _allocate(dated, per_day, today, edits) if dated else []
    ordered = order + sorted((e for e in entries if e['daysLeft'] is None), key=lambda e: e['target'])
    if edits:
        notes.append('Prioridad elegida por el alumno: ' + ' → '.join(edits) + '. La asignación de minutos se recalculó con ese orden.')
    if not entries and not undated:
        notes.append('Sin parciales ni entregas con fecha en el Margen: no se inventan fechas.')
    return {'policyVersion': POLICY_VERSION, 'today': today.isoformat(), 'rooms': room_titles,
            'exams': ordered, 'undated': undated, 'emergency': any(e['plan']['emergency'] for e in ordered),
            'primary': ordered[0]['target'] if ordered else None,
            'availability': {'perDay': per_day, 'sources': sources, 'declared': any(v > 0 for v in per_day.values())},
            'notes': notes}


def _make_entry(room_id, state, course, event, statuses, difficulty_by_lesson, topics, declared_notes, today):
    key = '|'.join((room_id, course['id'], event['id']))
    try:
        event_date = date.fromisoformat(event['date'])
    except (ValueError, KeyError, TypeError):
        return _invalid_event_entry(room_id, state, course, event)
    temario = temario_of(course, topics.get(key))
    read = readiness(temario, statuses)
    pendings = pending_lessons(course, temario, statuses)
    self_report = note_difficulty(declared_notes, course.get('title'))
    prepared = [{'id': l['id'], 'title': l.get('title', l['id']), 'minutes': int(l.get('minutes', 0) or 0),
                 'priority': l.get('priority', 3), 'difficulty': difficulty_by_lesson[l['id']]['level'],
                 'needsPractice': bool(self_report['needsPractice'])} for l in pendings]
    required = sum(l['minutes'] for l in prepared)
    level = max((l['difficulty'] for l in prepared), default=0)
    uncertainty = list(temario['uncertain'])
    if required and any(not l['minutes'] for l in pendings):
        uncertainty.append('Hay lecciones sin minutos declarados; no se inventa duración.')
    if course.get('title') is None:
        uncertainty.append('Curso sin título declarado.')
    return {'target': '|'.join((room_id, course['id'], event['id'])),
            'roomId': room_id, 'roomTitle': state['roomTitle'],
            'courseId': course['id'], 'courseTitle': course.get('title', course['id']),
            'eventId': event['id'], 'kind': event['kind'], 'title': event['title'],
            'date': event.get('date'), 'daysLeft': (event_date - today).days,
            'temario': {'source': temario['source'], 'lessonIds': temario['lessonIds']},
            'temarioReadiness': read, 'pendingLessons': prepared, 'minutesRequired': required,
            'minutesWindow': None, 'minutesAvailable': None, 'minutesAllocated': None, 'minutesDeficit': 0,
            'difficulty': {'level': level, 'selfReport': self_report, 'declaredErrors': self_report['declaredErrors'],
                           'needsPractice': self_report['needsPractice']},
            'uncertainty': uncertainty}


def _invalid_event_entry(room_id, state, course, event):
    entry = _stub_entry(room_id, state, {'id': event.get('id'), 'title': event.get('title')}, {'materia': course.get('title', '')})
    entry.update({'courseId': course['id'], 'courseTitle': course.get('title', course['id']), 'eventId': event.get('id'),
                  'kind': event.get('kind'), 'title': event.get('title'), 'date': event.get('date')})
    return entry


def _make_note_entry(room_id, state, note, study, declared_notes, today):
    """Parcial declarado en apuntes: fecha y alcance del alumno, con su incertidumbre explícita."""
    try:
        event_date = date.fromisoformat(study['parcialDate'])
    except (ValueError, KeyError):
        return _stub_entry(room_id, state, note, study)
    self_report = note_difficulty(declared_notes, study.get('materia'))
    return {'target': '|'.join((room_id, 'note', str(note.get('id')))),
            'roomId': room_id, 'roomTitle': state['roomTitle'], 'courseId': None, 'courseTitle': study.get('materia', ''),
            'eventId': None, 'noteId': note.get('id'), 'kind': 'study', 'title': note.get('title', study.get('materia')),
            'date': study['parcialDate'], 'daysLeft': (event_date - today).days,
            'temario': {'source': 'notes', 'lessonIds': []},
            'temarioReadiness': {'mastered': 0, 'total': 0, 'ratio': 0.0, 'source': 'notes'},
            'pendingLessons': [], 'minutesRequired': 0, 'difficulty': {'level': 0, 'selfReport': self_report,
                                                                     'declaredErrors': self_report['declaredErrors'],
                                                                     'needsPractice': self_report['needsPractice']},
            'uncertainty': ['Fecha de parcial declarada en apuntes del alumno; el alcance se organiza con el MCP de autoría.']}


def _stub_entry(room_id, state, note, study):
    return {'target': '|'.join((room_id, 'note', str(note.get('id')))), 'roomId': room_id, 'roomTitle': state['roomTitle'],
            'courseId': None, 'courseTitle': study.get('materia', ''), 'eventId': None, 'noteId': note.get('id'),
            'kind': 'study', 'title': note.get('title', study.get('materia')), 'date': study.get('parcialDate'),
            'daysLeft': None, 'temario': {'source': 'notes', 'lessonIds': []},
            'temarioReadiness': {'mastered': 0, 'total': 0, 'ratio': 0.0, 'source': 'notes'},
            'pendingLessons': [], 'minutesRequired': 0, 'minutesWindow': 0, 'minutesAvailable': 0,
            'minutesAllocated': 0, 'minutesDeficit': 0,
            'priorityScore': 0, 'priorityReasons': ['Fecha inválida declarada en apuntes; no se inventa corrección.'],
            'difficulty': {'level': 0, 'selfReport': None, 'declaredErrors': 0, 'needsPractice': False},
            'uncertainty': ['La fecha registrada no es válida; se declara y no se corrige por cuenta del sistema.'],
            'plan': {'cover': [], 'postponed': [], 'emergency': False, 'declaredMinutes': False, 'note': None}}


# ------------------------------------------------------------------ modo efectivo

def _context_exam(entry, declared_minutes):
    pressured = bool(declared_minutes) and entry['minutesRequired'] > entry['minutesAvailable']
    return {'target': entry['target'], 'daysLeft': entry['daysLeft'], 'kind': entry['kind'],
            'readiness': {'ratio': entry['temarioReadiness']['ratio'], 'uncertain': entry['temario']['source'] != 'confirmed'},
            'pendingLessons': entry['pendingLessons'], 'difficulty': entry['difficulty']['level'],
            'pressure': {'required': entry['minutesRequired'], 'available': entry['minutesAvailable'], 'insufficient': pressured,
                         'measured': bool(declared_minutes)}}


def effective_mode(preference, context, last_mode=None):
    """Decisión determinista del modo según preferencia y realidad del Margen (sin suponer urgencia).

    Q1: en auto, un parcial/deadline dentro de URGENT_DAYS sin dominio acreditado
    (preparación < URGENT_READINESS), o con presión de tiempo medida (faltan
    minutos declarados), baja automáticamente a Flexible con aviso y motivos.
    La preferencia manual persiste como override: sin rebote al auto. En la
    primera visita (last_mode None) no hay aviso de transición ni se supone un
    modo anterior.
    """
    preference = normalize_preference(preference if isinstance(preference, dict) else {'choice': 'auto'}, today=context.get('today'))
    reasons = []
    if preference['choice'] == 'manual':
        mode = preference['mode']
        reasons.append('Preferencia manual del alumno: ' + mode + '. La política automática no reemplaza este override.')
        return {'choice': 'manual', 'mode': mode, 'effectiveMode': mode,
                'changed': bool(last_mode and last_mode != mode), 'reasons': reasons, 'notice': None,
                'version': POLICY_VERSION, 'overrideActive': True, 'requirements': mode_requirements(mode)}
    exams = [e for e in context.get('exams', []) if isinstance(e.get('daysLeft'), int) and 0 <= e['daysLeft'] <= URGENT_DAYS]
    insecure, pressured = [], []
    for exam in exams:
        prep = exam.get('readiness', {})
        if prep.get('uncertain') or prep.get('ratio', 1) < URGENT_READINESS:
            insecure.append(exam)
        elif exam.get('pressure', {}).get('insufficient'):
            pressured.append(exam)
    remaining = [e for e in context.get('exams', []) if e not in exams]
    emergency_soon = [e for e in context.get('exams', []) if 0 <= (e.get('daysLeft') or 10 ** 6) <= SOON_DAYS and e.get('pressure', {}).get('insufficient')]
    if insecure or pressured:
        mode = 'flexible'
        for exam in insecure:
            preparacion = 'temario sin confirmar' if exam['readiness'].get('uncertain') else 'preparación ' + format(exam['readiness'].get('ratio', 0), '.2')
            reasons.append('Plazo próximo sin dominio acreditado: %s, faltan %d día(s) (%s).' % (exam['target'], exam['daysLeft'], preparacion))
        for exam in pressured:
            reasons.append('Presión de tiempo medida: %s necesita %d min y sólo hay %d declarados antes del plazo.' % (
                exam['target'], exam['pressure']['required'], exam['pressure']['available']))
        reasons.append('Cambio automático a Flexible para avanzar conservando pendientes; la puerta de evidencia no cambia.')
    elif emergency_soon or any(e.get('pendingLessons') for e in context.get('exams', [])):
        mode = 'strict'
        if emergency_soon:
            reasons.append('El tiempo declarado no alcanza en los próximos %d días: Estricto con pendientes explícitos.' % SOON_DAYS)
        elif exams:
            reasons.append('Compromisos en %d días con pendientes o temario sin confirmar: Estricto.' % SOON_DAYS)
        else:
            reasons.append('Hay temas pendientes de acreditar en el Margen: Estricto.')
    else:
        mode = 'extreme'
        reasons.append('Sin compromiso cercano sin acreditación: consolidar con transferencia y contraejemplos (Extremo).')
    if context.get('uncertainty'):
        reasons.append('Incertidumbres declaradas, sin inventar urgencia: ' + '; '.join(context['uncertainty'][:3]))
    changed = last_mode is not None and last_mode != mode
    notice = None
    if changed:
        notice = ('Modo automático cambió de ' + last_mode + ' a ' + mode + '. Motivos: ' + ' '.join(reasons) +
                  ' Podés fijar manual o volver cuando quieras; el override manual persiste hasta reactivar auto.')
    return {'choice': 'auto', 'mode': None, 'effectiveMode': mode, 'changed': changed, 'reasons': reasons,
            'notice': notice, 'version': POLICY_VERSION, 'overrideActive': False,
            'remainingExams': [e['target'] for e in remaining], 'requirements': mode_requirements(mode)}


def evaluate_mode(server, today=None, consume_notice=True):
    """Alto nivel: preferencia persistida + contexto real; registra el aviso UNA vez por cambio real.

    `consume_notice=False` deja el aviso pendiente: lo usan briefs de contexto
    (por ejemplo el de autoría) que no son el canal del estudiante y no deben
    gastar la única entrega del aviso.
    """
    state = read_state(server)
    preference = state.get('preference') if isinstance(state.get('preference'), dict) else {'choice': 'auto'}
    context = plan_context(server, today=today)
    decision = effective_mode(preference, context, last_mode=state.get('lastEffectiveMode'))
    if decision['changed']:
        state['notice'] = {'from': state.get('lastEffectiveMode'), 'to': decision['effectiveMode'],
                           'reasons': decision['reasons'], 'at': context['today'], 'delivered': False}
        state['lastEffectiveMode'] = decision['effectiveMode']
        write_state(server, state)
    # El aviso se entrega UNA vez por cambio real y no se repite en cada render.
    notice = state.get('notice')
    if isinstance(notice, dict) and not notice.get('delivered'):
        if not consume_notice:
            return {'decision': decision, 'notice': notice, 'preference': read_preference(server), 'context': context}
        notice['delivered'] = True
        state['notice'] = notice
        write_state(server, state)
        return {'decision': decision, 'notice': notice, 'preference': read_preference(server), 'context': context}
    return {'decision': decision, 'notice': None, 'preference': read_preference(server), 'context': context}


def mode_brief(server, today=None, consume_notice=True):
    """Bloque de modo para briefs de ambos MCP: instrucciones ANTES de generar + requisitos y avisos."""
    evaluated = evaluate_mode(server, today=today, consume_notice=consume_notice)
    decision = evaluated['decision']
    return {'effectiveMode': decision['effectiveMode'], 'choice': decision['choice'],
            'policyVersion': POLICY_VERSION, 'instructions': mode_prompt(decision['effectiveMode']),
            'requirements': decision['requirements'], 'reasons': decision['reasons'],
            'notice': evaluated['notice'], 'scope': 'Política local determinista del Margen; sin proveedores.'}


def acknowledge_notice(server):
    """Marca el aviso como visto; no se repite en cada render."""
    state = read_state(server)
    if isinstance(state.get('notice'), dict):
        state['notice']['delivered'] = True
        write_state(server, state)
    return {'acknowledged': True}


# ------------------------------------------------------------------ API de alto nivel con scopes

def open_states(server, today=None):
    """Snapshots de los pliegos del Margen con las APIs existentes; nunca mezcla históricos.

    Defensivo: un pliego ilegible no debe romper al tutor; se declara la omisión.
    """
    states = []
    for target in scopes(server):
        try:
            with _Scoped(server, target['scope']):
                state = server.snapshot()
        except Exception as exc:  # pliego ilegible: se declara, no se inventa
            states.append({'roomId': target['id'], 'roomTitle': target['title'], 'courses': [], 'events': [],
                           'calendarEvents': [], 'settings': {}, 'notes': [], 'error': str(exc)})
            continue
        state['roomId'] = target['id']
        state['roomTitle'] = target['title']
        state['notes'] = state.get('library', {}).get('notes', [])
        state['today'] = today or state.get('localDate')
        states.append(state)
    return states


def build_global_plan(server, today=None):
    """Plan global con todos los parciales, temarios y ediciones reales del Margen elegido."""
    today = today or date.today().isoformat()
    states = open_states(server, today=today)
    for state in states:
        state['today'] = today
    topics = read_exam_topics(server)
    edits = read_plan_edits(server)
    plan = plan_from_states(states, today=today, topics=topics, edits=edits)
    omitted = [state['roomId'] for state in states if state.get('error')]
    if omitted:
        plan['notes'].append('Pliegos omitidos por error de apertura: ' + ', '.join(omitted) + '.')
    return plan


def plan_context(server, today=None):
    """Contexto de decisión: fechas, preparación, presión medida e incertidumbres reales.

    Si el Margen no se puede leer, no se inventa urgencia: el modo cae a la
    preferencia y el resto se declara como incertidumbre.
    """
    try:
        plan = build_global_plan(server, today=today)
    except Exception:
        return {'today': today or date.today().isoformat(), 'exams': [], 'anyPending': False,
                'uncertainty': ['No se pudo leer el plan del Margen; no se inventa urgencia de tiempo.']}
    exams, uncertain, any_pending = [], list(plan['notes']), False
    for entry in plan['exams']:
        if entry['daysLeft'] is None:
            uncertain.extend(entry['uncertainty'])
            continue
        exams.append(_context_exam(entry, plan['availability']['declared']))
        uncertain.extend(entry['uncertainty'])
        any_pending = any_pending or bool(entry['pendingLessons'])
    for item in plan.get('undated', []):
        uncertain.extend(item['uncertainty'])
    return {'today': plan['today'], 'exams': exams, 'anyPending': any_pending, 'uncertainty': uncertain}


def effective_now(server, today=None):
    """Atajo determinista: preferencia persistida + contexto real → modo efectivo con requisitos."""
    return effective_mode(read_preference(server), plan_context(server, today=today))
