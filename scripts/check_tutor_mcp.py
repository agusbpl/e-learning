"""Comprobación de integración real del MCP de tutor externo por stdio, con base temporal."""
import asyncio
import json
from pathlib import Path
import os
import sys
import tempfile
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests' / 'helpers'))
from fixture_workspace import build, fixture_course


def payload(result):
    assert not result.is_error, result
    if result.structured_content is not None:
        return result.structured_content
    return json.loads(result.content[0].text)


async def main():
    with tempfile.TemporaryDirectory(prefix='tutor-mcp-check-') as directory:
        fixture_root = build(Path(directory) / 'fixture-root')
        data = Path(directory) / 'data'
        data.mkdir()
        os.environ['LEARNING_DATA_DIR'] = str(data)
        os.environ['OPENROUTER_API_KEY'] = ''
        import server
        server.ROOT = fixture_root
        server.init_db()
        course = fixture_course()
        cid, lid = course['id'], course['lessons'][0]['id']
        exercises = [e['id'] for e in course['lessons'][0]['exercises']]
        settings = {'LEARNING_DATA_DIR': str(data), 'OPENROUTER_API_KEY': ''}
        parameters = StdioServerParameters(command=sys.executable, args=[str(fixture_root / 'tutor_mcp.py')],
                                           env={**os.environ, **settings})
        async with Client(parameters) as client:
            tools = await client.list_tools()
            names = {t.name for t in tools.tools}
            assert {'list_pliegos', 'open_pliego', 'tutor_courses', 'tutor_brief', 'tutor_conversation',
                    'register_tutor_exchange', 'tutor_pending', 'tutor_note_brief', 'register_note_exchange'} <= names
            assert 'save_course_draft' not in names and 'author_brief' not in names, 'El MCP de tutor no debe exponer herramientas de autoría.'

            listing = payload(await client.call_tool('list_pliegos', {}))
            assert any(r['id'] == 'local' for r in listing['rooms'])
            courses = payload(await client.call_tool('tutor_courses', {}))
            assert courses['courses'][0]['lessons'][0]['status'] == 'unseen'
            assert not courses['courses'][0]['lessons'][0]['status'] == 'independent'

            brief = payload(await client.call_tool('tutor_brief', {'course_id': cid, 'lesson_id': lid}))
            assert brief['courseVersion'] == course['version']
            assert len(brief['contextHash']) == 64
            assert brief['manifest']['historyIncluded']
            assert all(e['status'] == 'pending' for e in brief['exercises'])
            assert 'register_tutor_exchange' in brief['contract'] and 'rúbrica' in brief['evaluationRules']

            # Pregunta y respuesta externa sin evaluación: queda pending, sin evento assessment.
            answer_text = 'Aplicación nueva independiente para ' + exercises[0] + ': registro y guardo en el pliego abierto.'
            first = payload(await client.call_tool('register_tutor_exchange', {
                'request_id': 'check-req-1', 'course_id': cid, 'lesson_id': lid,
                'question': '¿Dónde conviene anotar? Mi aplicación: ' + answer_text,
                'reply': 'Anotá en la lección abierta; la copia quedaría en otra pliego.',
                'model_name': 'agente-externo/contador-check',
                'exercise_id': exercises[0],
                'context_hash': brief['contextHash']}))
            assert not first['alreadyRegistered'] and first['status'] == 'pending'
            assert first['contextHashVerified'], 'El hash del brief debe verificarse cuando no cambió la selección.'
            assert first['assessmentEventId'] is None and not first['noteEventIds']

            # Idempotencia: repetir el mismo request_id con los mismos argumentos no duplica;
            # con otro contenido (respuesta, pregunta, target o evaluación) se rechaza.
            repeat = payload(await client.call_tool('register_tutor_exchange', {
                'request_id': 'check-req-1', 'course_id': cid, 'lesson_id': lid,
                'question': '¿Dónde conviene anotar? Mi aplicación: ' + answer_text,
                'reply': 'Anotá en la lección abierta; la copia quedaría en otra pliego.',
                'exercise_id': exercises[0],
                'model_name': 'agente-externo/contador-check'}))
            assert repeat['alreadyRegistered']
            for attempt in ({'reply': ' otra respuesta'}, {'question': '¿Otra pregunta?'},
                            {'exercise_id': exercises[1]}, {'assessment': {'status': 'with_help', 'gaps': ['x']}}):
                blocked = await client.call_tool('register_tutor_exchange', {
                    'request_id': 'check-req-1', 'course_id': cid, 'lesson_id': lid,
                    'question': '¿Dónde conviene anotar? Mi aplicación: ' + answer_text,
                    'reply': 'Anotá en la lección abierta; la copia quedaría en otra pliego.',
                    'model_name': 'agente-externo/contador-check', **attempt})
                assert blocked.is_error
            version_block = await client.call_tool('register_tutor_exchange', {
                'request_id': 'check-req-ver', 'course_id': cid, 'lesson_id': lid,
                'question': '¿Se registra igual?', 'reply': 'No.', 'model_name': 'agente-externo/contador-check',
                'expected_course_version': '9.9.9'})
            assert version_block.is_error and 'versión' in version_block.content[0].text

            # Respuestas de actividad se registran por la interfaz local; con todas respondidas y
            # citas literales de la aplicación, la evaluación externa puede indicar independent.
            state = server.snapshot()
            with server.connect() as conn:
                # Simulo las respuestas de actividades tal como las guarda la interfaz.
                for exercise_id in exercises:
                    exercise = next(e for e in course['lessons'][0]['exercises'] if e['id'] == exercise_id)
                    body = {'exerciseId': exercise_id, 'courseVersion': course['version']}
                    if exercise['type'] == 'choice':
                        body['reasoning'] = 'Justificación nueva del estudiante para ' + exercise_id + '.'
                    else:
                        body['text'] = 'Aplicación textual nueva del estudiante para ' + exercise_id + '.'
                    conn.execute('INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?)',
                                 ('check-asn-' + exercise_id, server.now(), 'answer', cid, lid, json.dumps(body, ensure_ascii=False)))
            full_evidence = []
            for exercise in course['lessons'][0]['exercises']:
                for criterion in exercise['rubric']:
                    field_quote = 'Justificación nueva del estudiante para ' + exercise['id'] + '.' if exercise['type'] == 'choice' \
                        else 'Aplicación textual nueva del estudiante para ' + exercise['id'] + '.'
                    full_evidence.append({'exerciseId': exercise['id'], 'criterion': criterion, 'result': 'met',
                                          'independent': True, 'quote': field_quote})
            second = payload(await client.call_tool('register_tutor_exchange', {
                'request_id': 'check-req-2', 'course_id': cid, 'lesson_id': lid,
                'question': 'Aplicación textual nueva del estudiante para ' + exercises[-1] + '.',
                'reply': 'Comprobar transferencia con otro caso; no repito la explicación.',
                'model_name': 'agente-externo/contador-check',
                'exercise_id': exercises[-1],
                'assessment': {'status': 'independent', 'evidence': ['Aplicación nueva'], 'nextAction': 'continue',
                               'criterionChecks': full_evidence}}))
            assert second['status'] == 'independent', second
            assert second['assessmentEventId']
            notes = json.dumps(payload(await client.call_tool('tutor_conversation', {'course_id': cid})), ensure_ascii=False)
            assert 'rawResponse' not in notes and 'tutorContext' not in notes
            assert 'Anotá en la lección abierta' in notes
            # Un registro interrumpido (solo la pregunta) permite reintentar sin duplicar.
            with server.connect() as conn:
                conn.execute("DELETE FROM events WHERE id='check-req-3'")
                conn.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?)",
                             ('check-req-3-pregunta', server.now(), 'chat_message', cid, lid,
                              json.dumps({'message': 'Pregunta interrumpida', 'courseVersion': course['version']}, ensure_ascii=False)))
            rescued = payload(await client.call_tool('register_tutor_exchange', {
                'request_id': 'check-req-3', 'course_id': cid, 'lesson_id': lid,
                'question': 'Pregunta interrumpida', 'reply': 'Respuesta observable del agente externo.',
                'model_name': 'agente-externo/contador-check'}))
            assert not rescued['alreadyRegistered']
            # La interfaz: helpReceived refleja la ayuda externa en la próxima respuesta.
        async with Client(parameters, mode='legacy') as client:
            brief = payload(await client.call_tool('tutor_brief', {'course_id': cid, 'lesson_id': lid}))
            assert brief['conversation'], 'El brief muestra la conversación registrada en el mismo pliego.'
        with server.connect() as conn:
            reply = json.loads(conn.execute("SELECT body FROM events WHERE id='check-req-1'").fetchone()['body'])
            assert reply['source'] == 'external-mcp'
            assert reply['tutorContext']['provider'] == 'external-mcp'
            assert reply['courseVersion'] == course['version']
            assessment = json.loads(conn.execute("SELECT body FROM events WHERE id=?", (second['assessmentEventId'],)).fetchone()['body'])
            assert assessment['status'] == 'independent' and assessment['criterionChecks']
        async with Client(parameters) as client:

            # --- Apuntes por el canal MCP: pendiente, brief y registro con trazabilidad ---
            note = server.library().save_note({'title': 'Apunte de check', 'folder': '', 'shared': False,
                                               'content': 'Texto personal del check para conversar con el tutor externo.'})
            record = server.note_tutor({'requestId': 'check-note-1', 'noteId': note['id'],
                                        'message': '¿Qué significa esta idea?', 'scope': 'general',
                                        'noteRevision': note['revision'], 'channel': 'mcp'})
            assert record['status'] == 'pending' and record['channel'] == 'mcp'
            pendings = payload(await client.call_tool('tutor_pending', {}))
            assert [p['requestId'] for p in pendings['notePendings']] == ['check-note-1']
            assert pendings['notePendings'][0]['message'] == '¿Qué significa esta idea?'
            note_brief = payload(await client.call_tool('tutor_note_brief', {'request_id': 'check-note-1'}))
            assert note_brief['context']['context']['studentText'] == note['content']
            assert note_brief['noteRevision'] == note['revision'] and not note_brief['noteRevisionChanged']
            assert 'register_note_exchange' in note_brief['noteContract']
            note_reply = payload(await client.call_tool('register_note_exchange', {
                'request_id': 'check-note-1', 'note_id': note['id'], 'question': '¿Qué significa esta idea?',
                'reply': 'La idea significa lo que tu apunte resume; contrástalo con la fuente citada.',
                'model_name': 'agente-externo/modelo-nota-check', 'context_hash': note_brief['contextHash']}))
            assert not note_reply['alreadyRegistered'] and note_reply['contextHashVerified']
            saved = server.library().snapshot()['noteTutor'][-1]
            assert saved['status'] == 'answered' and saved['model'] == 'agente-externo/modelo-nota-check'
            assert json.dumps(saved, ensure_ascii=False).count('rawResponse') == 0
            repeat_note = payload(await client.call_tool('register_note_exchange', {
                'request_id': 'check-note-1', 'note_id': note['id'], 'question': '¿Qué significa esta idea?',
                'reply': 'La idea significa lo que tu apunte resume; contrástalo con la fuente citada.',
                'model_name': 'agente-externo/modelo-nota-check', 'context_hash': note_brief['contextHash']}))
            assert repeat_note['alreadyRegistered']
            for attempt in ({'reply': 'Otra respuesta distinta.'}, {'note_id': note['id'] + '-x'},
                            {'question': 'Otra pregunta.'}):
                args = {'request_id': 'check-note-1', 'note_id': note['id'], 'question': '¿Qué significa esta idea?',
                        'reply': 'La idea significa lo que tu apunte resume; contrástalo con la fuente citada.',
                        'model_name': 'agente-externo/modelo-nota-check'}
                args.update(attempt)
                blocked = await client.call_tool('register_note_exchange', args)
                assert blocked.is_error
            independent_block = await client.call_tool('register_note_exchange', {
                'request_id': 'check-note-2', 'note_id': note['id'], 'question': 'Registrá directo.',
                'reply': 'Respuesta.', 'model_name': 'agente-externo/modelo-nota-check',
                'assessment': {'status': 'independent'}})
            assert independent_block.is_error and 'dominio' in independent_block.content[0].text
            # Consulta de apunte sin responder + bóveda sin cursos: el MCP sigue funcionando.
            server.note_tutor({'requestId': 'check-note-2', 'noteId': note['id'], 'message': 'Consulta nueva.',
                               'scope': 'general', 'noteRevision': note['revision'], 'channel': 'mcp'})
            with server.connect() as conn:
                conn.execute('DELETE FROM events')
                conn.execute('DELETE FROM courses')
            # El apunte sigue existiendo como archivo Markdown original en Apuntes/.
            original = server.library().note_file(note['id'])
            assert original is not None and original.is_file()
            empty_courses = payload(await client.call_tool('tutor_courses', {}))
            assert empty_courses['courses'] == []
            without_courses = payload(await client.call_tool('tutor_pending', {}))
            assert [p['requestId'] for p in without_courses['notePendings']] == ['check-note-2']
            brief_2 = payload(await client.call_tool('tutor_note_brief', {'request_id': 'check-note-2'}))
            assert brief_2['context']['context']['studentText'] == note['content']
            answer_2 = payload(await client.call_tool('register_note_exchange', {
                'request_id': 'check-note-2', 'note_id': note['id'], 'question': 'Consulta nueva.',
                'reply': 'Respuesta del agente externo en bóveda sin cursos.',
                'model_name': 'agente-externo/modelo-nota-check', 'context_hash': brief_2['contextHash']}))
            assert answer_2['contextHashVerified']
    print('MCP tutor stdio (handshake actual y legacy): lecciones (brief, privacidad, registro atómico con trazabilidad, puerta de evidencia, idempotencia) y apuntes (pendientes, brief de nota, registro sin acreditar dominio, bóveda sin cursos) OK. Base temporal eliminada.')


if __name__ == '__main__':
    asyncio.run(main())
