"""Explicit feedback handoffs; the MCP client supplies the authoring model."""
import json
import uuid


def pending(state, course_id=''):
    finished = {e['data'].get('requestId') for e in state['events'] if e['kind'] == 'continuation_applied'}
    return [e for e in state['events'] if e['kind'] == 'continuation_requested' and e['id'] not in finished
            and (not course_id or e['courseId'] == course_id)]


def activate(server, request_id, course, expected_version, rationale):
    if not isinstance(rationale, str) or not 8 <= len(rationale.strip()) <= 4000:
        raise ValueError('Justificá la continuación con evidencia y prioridades, hasta 4000 caracteres.')
    server.validate_course(course)
    with server.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        request = conn.execute("SELECT * FROM events WHERE id=? AND kind='continuation_requested'", (request_id,)).fetchone()
        if not request or request['course_id'] != course['id']:
            raise ValueError('Elegí un encargo explícito de continuación de este curso.')
        for row in conn.execute("SELECT * FROM events WHERE kind='continuation_applied' AND course_id=?", (course['id'],)):
            previous = server.unpack(row)
            if previous['data'].get('requestId') == request_id:
                return {'applied': True, 'alreadyApplied': True, **previous['data']}
        row = conn.execute('SELECT body FROM courses WHERE id=?', (course['id'],)).fetchone()
        old = json.loads(row['body']) if row else None
        if not old or old['version'] != expected_version or json.loads(request['body']).get('courseVersion') != expected_version:
            raise ValueError('El curso cambió desde el encargo. Generá un nuevo encargo con el contexto actual.')
        if course['version'] == expected_version:
            raise ValueError('La continuación requiere una versión nueva.')
        if not {l['id'] for l in old['lessons']} <= {l['id'] for l in course['lessons']}:
            raise ValueError('Conservá las lecciones existentes y sus IDs al preparar la continuación.')
        metadata = {'requestId': request_id, 'previousVersion': expected_version, 'newVersion': course['version'],
                    'rationale': rationale.strip(), 'sourceEventIds': json.loads(request['body']).get('sourceEventIds', [])}
        records = [('course_version', '', {'previousCourse': old, 'newVersion': course['version']}),
                   ('continuation_applied', request['lesson_id'], metadata)]
        for kind, lesson_id, data in records:
            conn.execute('INSERT INTO events VALUES(?,?,?,?,?,?)',
                         (str(uuid.uuid4()), server.now(), kind, course['id'], lesson_id, json.dumps(data, ensure_ascii=False)))
        conn.execute('UPDATE courses SET body=? WHERE id=?', (json.dumps(course, ensure_ascii=False), course['id']))
    server.library().initialize([course])
    return {'applied': True, 'alreadyApplied': False, **metadata}
