"""Pruebas del MCP de tutor externo con base temporal; nunca consultan un proveedor."""
import json
import sys
import tempfile
import threading
import unittest
from unittest import mock
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests' / 'helpers'))
import server  # noqa: E402
from fixture_workspace import build  # noqa: E402

try:
    import tutor_mcp
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError as exc:  # el runtime del MCP vive en .venv-author
    tutor_mcp, MISSING = None, exc
else:
    MISSING = None

NEEDS_MCP = unittest.skipIf(tutor_mcp is None, 'mcp no disponible: correr con .venv-author/bin/python')


@NEEDS_MCP
class TutorMcpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='tutor-mcp-tests-')
        cls.old_db, cls.old_data, cls.old_root, cls.old_key, cls.old_port = server.DB, server.DATA, server.ROOT, server.KEY, server.PORT
        server.ROOT = build(Path(cls.tmp.name) / 'fixture-root')
        server.DATA = Path(cls.tmp.name)
        server.DB = Path(cls.tmp.name) / 'test.sqlite3'
        server.KEY = ''
        server.init_db()
        cls.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        server.PORT = cls.http.server_address[1]
        cls.base = 'http://127.0.0.1:' + str(cls.http.server_address[1])
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        server.DB, server.DATA, server.ROOT, server.KEY, server.PORT = cls.old_db, cls.old_data, cls.old_root, cls.old_key, cls.old_port
        cls.tmp.cleanup()

    def setUp(self):
        with server.connect() as con:
            con.execute('DELETE FROM events')
            con.execute('DELETE FROM courses')
            for table in ('documents', 'notes', 'note_versions', 'course_drafts', 'annotation_revisions', 'note_tutor', 'tutor_contexts', 'calendar_events'):
                con.execute('DELETE FROM ' + table)
        server.init_db()
        self.course = server.snapshot()['courses'][0]
        self.cid = self.course['id']
        self.lid = self.course['lessons'][0]['id']
        self.exercises = {e['id']: e for e in self.course['lessons'][0]['exercises']}

    def post_event(self, kind, data, event_id=None):
        payload = {'kind': kind, 'courseId': self.cid, 'lessonId': self.lid, 'data': data}
        if event_id:
            payload['id'] = event_id
        request = Request(self.base + '/api/event', data=json.dumps(payload).encode(),
                          headers={'Content-Type': 'application/json'})
        try:
            return json.load(urlopen(request))
        except Exception as exc:  # pragma: no cover - report the server message directly
            self.fail('POST /api/event falló: %s' % exc)

    def course_pending(self, request_id, message):
        """Crea el pendiente exactamente como la interfaz del canal MCP externo."""
        return self.post_event('chat_message', {'message': message, 'exerciseId': None,
                                                'channel': 'mcp', 'pendingExternal': True},
                               event_id=request_id + '-pregunta')

    def save_note(self, **overrides):
        body = {'title': 'Apunte temporal', 'folder': '', 'content': 'Idea central personal para repasar.',
                'shared': False}
        body.update(overrides)
        return server.library().save_note(body)

    def note_pending(self, note, request_id='note-req-1', message='¿Qué significa esta idea?', **overrides):
        """Consulta de apunte por el canal MCP, igual que la interfaz (server.note_tutor)."""
        body = {'requestId': request_id, 'noteId': note['id'], 'message': message,
                'scope': 'general', 'noteRevision': note['revision'], 'channel': 'mcp'}
        body.update(overrides)
        request = Request(self.base + '/api/note-tutor', data=json.dumps(body).encode(),
                          headers={'Content-Type': 'application/json'})
        try:
            return json.load(urlopen(request))
        except Exception as exc:  # pragma: no cover - report the server message directly
            self.fail('POST /api/note-tutor falló: %s' % exc)

    def note_records(self):
        with server.library().connect() as conn:
            return {row['id']: json.loads(row['body']) for row in conn.execute('SELECT id, body FROM note_tutor')}

    def register(self, **overrides):
        args = {'request_id': 'req-999', 'course_id': self.cid, 'lesson_id': self.lid,
                'question': '¿Cómo decido dónde guardar mis anotaciones?',
                'reply': 'Anotalas en la lección que abriste directamente; la copia seguiría en otro pliego.',
                'model_name': 'agente-prueba/test-modelo'}
        args.update(overrides)
        return tutor_mcp.register_tutor_exchange(**args)

    def kind_count(self, kind):
        return [e for e in server.snapshot()['events'] if e['courseId'] == self.cid and e['kind'] == kind]

    def test_tutor_courses_lists_lessons_and_state(self):
        result = tutor_mcp.tutor_courses()
        course = result['courses'][0]
        self.assertEqual(course['id'], self.cid)
        self.assertEqual([l['id'] for l in course['lessons']], [l['id'] for l in self.course['lessons']])
        self.assertEqual(course['lessons'][0]['status'], 'unseen')

    def test_tutor_brief_context_rules_and_privacy(self):
        server.event('annotation', self.cid, self.lid, {'comment': 'DUDA COMPARTIDA', 'shareWithTutor': True})
        server.event('annotation', self.cid, self.lid, {'comment': 'NO EXPONER PRIVADA', 'shareWithTutor': False})
        brief = tutor_mcp.tutor_brief(course_id=self.cid, lesson_id=self.lid)
        text = json.dumps(brief, ensure_ascii=False)
        self.assertIn('DUDA COMPARTIDA', text)
        self.assertNotIn('NO EXPONER PRIVADA', text)
        self.assertIn('rúbrica', brief['evaluationRules'])
        self.assertEqual(len(brief['contextHash']), 64)
        self.assertEqual(brief['contextRevision'], 0)
        self.assertTrue(brief['manifest']['items'])
        self.assertIn('register_tutor_exchange', brief['contract'])
        self.assertEqual([e['status'] for e in brief['exercises']], ['pending'] * len(self.exercises))
        self.assertEqual(brief['context']['studentMessage'], '')

    def test_register_rejects_missing_reply_or_model(self):
        with self.assertRaises(ToolError):
            self.register(reply='')
        with self.assertRaises(ToolError):
            self.register(model_name=' ')
        with self.assertRaises(ToolError):
            self.register(request_id='id inválido')
        self.assertEqual(self.kind_count('tutor_reply'), [])
        self.assertEqual(self.kind_count('chat_message'), [])

    def test_register_exchange_plain_idempotent_and_traced(self):
        result = self.register()
        self.assertEqual(result['status'], 'pending')
        self.assertEqual(result['questionEventId'], 'req-999-pregunta')
        self.assertEqual(result['replyEventId'], 'req-999')
        self.assertFalse(result['contextHashVerified'])
        self.assertEqual(len(self.kind_count('tutor_reply')), 1)
        self.assertEqual(len(self.kind_count('chat_message')), 1)
        self.assertEqual(self.kind_count('assessment'), [])
        again = self.register()
        self.assertTrue(again['alreadyRegistered'])
        self.assertEqual(len(self.kind_count('tutor_reply')), 1)
        reply = self.kind_count('tutor_reply')[0]
        self.assertEqual(reply['data']['source'], 'external-mcp')
        self.assertEqual(reply['data']['model'], 'agente-prueba/test-modelo')
        self.assertEqual(reply['data']['courseVersion'], self.course['version'])
        self.assertEqual(reply['data']['tutorContext']['provider'], 'external-mcp')
        self.assertEqual(reply['data']['tutorContext']['contextHash'], result['contextHash'])
        with self.assertRaises(ToolError):
            self.register(question='¿Otra pregunta distinta?')
        self.assertEqual(len(self.kind_count('tutor_reply')), 1)

    def test_register_blocked_when_course_version_changed(self):
        with self.assertRaises(ToolError):
            self.register(expected_course_version='9.9.9')
        self.assertEqual(self.kind_count('tutor_reply'), [])
        self.assertEqual(self.kind_count('chat_message'), [])

    def test_register_independent_without_all_answers_stays_pending(self):
        exercise_id = next(iter(self.exercises))
        quote = '¿Cómo decido dónde guardar mis anotaciones?'
        result = self.register(assessment={'status': 'independent', 'evidence': ['Relación señalada'],
                                           'criterionChecks': [{'exerciseId': exercise_id,
                                                                'criterion': self.exercises[exercise_id]['rubric'][0],
                                                                'result': 'met', 'independent': True, 'quote': quote}]})
        self.assertEqual(result['status'], 'pending')
        assessment = self.kind_count('assessment')[0]
        self.assertIn('Faltan actividades', assessment['data']['reason'])

    def test_register_independent_with_full_evidence_is_recorded(self):
        texts = {}
        for exercise_id, exercise in self.exercises.items():
            field = 'reasoning' if exercise['type'] == 'choice' else 'text'
            texts[exercise_id] = 'Aplicación nueva independiente para ' + exercise_id + ': guardo en el pliego abierto.'
            self.post_event('answer', {'exerciseId': exercise_id, field: texts[exercise_id]})
        checks = [{'exerciseId': exercise_id, 'criterion': criterion, 'result': 'met', 'independent': True,
                   'quote': texts[exercise_id]}
                  for exercise_id, exercise in self.exercises.items() for criterion in exercise['rubric']]
        result = self.register(assessment={'status': 'independent', 'evidence': ['Aplicación nueva'],
                                           'nextAction': 'continue', 'criterionChecks': checks})
        self.assertEqual(result['status'], 'independent')
        assessment = self.kind_count('assessment')[0]
        self.assertEqual(assessment['data']['status'], 'independent')
        self.assertEqual(assessment['data']['nextAction'], 'continue')
        self.assertIn('evaluationPolicyVersion', assessment['data'])

    def test_register_rejects_damaged_assessment_and_writes_nothing(self):
        with self.assertRaises(ToolError):
            self.register(assessment={'status': 'aprobado'})
        with self.assertRaises(ToolError):
            self.register(assessment={'status': 'pending', 'evidence': [42]})
        self.assertEqual(self.kind_count('tutor_reply') + self.kind_count('chat_message'), [])

    def test_evidence_gate_excludes_helped_answer_quotes(self):
        texts = {}
        for exercise_id in self.exercises:
            texts[exercise_id] = 'Aplicación nueva independiente para ' + exercise_id
        self.register(request_id='req-previa', question='Primera explicación del tutor.',
                      reply='Explicación de ayuda del agente externo.')
        for exercise_id, exercise in self.exercises.items():
            field = 'reasoning' if exercise['type'] == 'choice' else 'text'
            item = self.post_event('answer', {'exerciseId': exercise_id, field: texts[exercise_id]})
            self.assertTrue(item['data']['helpReceived'], 'La ayuda externa previa debe marcar la respuesta como asistida.')
        checks = [{'exerciseId': exercise_id, 'criterion': criterion, 'result': 'met', 'independent': True,
                   'quote': texts[exercise_id]}
                  for exercise_id, exercise in self.exercises.items() for criterion in exercise['rubric']]
        result = self.register(request_id='req-post-ayuda', assessment={'status': 'independent', 'criterionChecks': checks})
        self.assertEqual(result['status'], 'pending')

    def test_evidence_gate_rejects_quote_not_from_student(self):
        for exercise_id in self.exercises:
            self.post_event('answer', {'exerciseId': exercise_id, 'text': 'respuesta mínima ' + exercise_id})
        exercise = next(iter(self.exercises.values()))
        checks = [{'exerciseId': exercise['id'], 'criterion': criterion, 'result': 'met', 'independent': True,
                   'quote': 'cita inventada por el tutor'} for criterion in exercise['rubric']]
        result = self.register(assessment={'status': 'independent', 'criterionChecks': checks})
        self.assertEqual(result['status'], 'pending')

    def test_conversation_pagination_and_sanitization(self):
        self.register(request_id='req-a')
        self.register(request_id='req-b')
        page = tutor_mcp.tutor_conversation(course_id=self.cid, lesson_id=self.lid, offset=0, limit=2)
        self.assertEqual(page['total'], 4)
        self.assertEqual(page['nextOffset'], 2)
        self.assertEqual([e['kind'] for e in page['events']], ['chat_message', 'tutor_reply'])
        rest = tutor_mcp.tutor_conversation(course_id=self.cid, lesson_id=self.lid, offset=2, limit=2)
        self.assertEqual([e['kind'] for e in rest['events']], ['chat_message', 'tutor_reply'])
        self.assertIsNone(rest['nextOffset'])
        sanitized = json.dumps(page, ensure_ascii=False)
        self.assertNotIn('tutorContext', sanitized)
        self.assertNotIn('rawResponse', sanitized)
        unfiltered = tutor_mcp.tutor_conversation(course_id=self.cid, lesson_id='')
        self.assertEqual(unfiltered['total'], 4)
        with self.assertRaises(ToolError):
            tutor_mcp.tutor_conversation(course_id=self.cid, lesson_id=self.lid, offset=-1)

    def test_notebook_entries_recorded_and_deduplicated(self):
        quote = 'Guardaré mis anotaciones en la lección abierta'
        proposal = [{'kind': 'decision', 'text': 'Decisión de repaso: la ubicación de las anotaciones dudosa', 'quote': quote}]
        result = self.register(request_id='req-note-1', question='Estoy dudando. ' + quote,
                               assessment={'status': 'pending', 'notebook': proposal})
        self.assertEqual(len(result['noteEventIds']), 1)
        second = self.register(request_id='req-note-2', question='Repito la duda: ' + quote + '. ¿Sigue abierta?',
                               assessment={'status': 'pending', 'notebook': proposal})
        self.assertEqual(second['noteEventIds'], [])
        self.assertEqual(len(self.kind_count('tutor_note')), 1)
        note = self.kind_count('tutor_note')[0]
        self.assertEqual(note['data']['author'], 'tutor')
        self.assertFalse(note['data']['isLearningEvidence'])

    def test_pending_lists_ui_question_and_registration_completes(self):
        message = '¿Cómo empiezo esta lección con pouco tiempo?'
        self.course_pending('ui-req-1', message)
        listing = tutor_mcp.tutor_pending()
        self.assertEqual([p['requestId'] for p in listing['coursePendings']], ['ui-req-1'])
        self.assertEqual(listing['coursePendings'][0]['message'], message)
        result = self.register(request_id='ui-req-1', question=message)
        self.assertFalse(result['alreadyRegistered'])
        question = self.kind_count('chat_message')[0]
        self.assertEqual(question['data']['channel'], 'mcp')
        self.assertTrue(question['data']['pendingExternal'], 'La fila de la interfaz debe conservarse sin sobrescribir.')
        self.assertEqual(len(self.kind_count('tutor_reply')), 1)
        self.assertEqual(tutor_mcp.tutor_pending()['coursePendings'], [])
        # Reintento idempotente del agente externo tras una respuesta perdida.
        again = self.register(request_id='ui-req-1', question=message)
        self.assertTrue(again['alreadyRegistered'])
        self.assertEqual(len(self.kind_count('tutor_reply')), 1)

    def test_register_rejects_wrong_question_for_ui_pending(self):
        self.course_pending('ui-req-2', 'Pregunta real del estudiante.')
        with self.assertRaises(ToolError):
            self.register(request_id='ui-req-2', question='Pregunta inventada por el agente.')
        self.assertEqual(self.kind_count('tutor_reply'), [])
        self.assertEqual(len(self.kind_count('chat_message')), 1)

    def test_register_identity_rejects_other_target_or_assessment(self):
        other_lesson = self.course['lessons'][1]['id']
        self.register(request_id='req-1')
        with self.assertRaises(ToolError):
            self.register(request_id='req-1', lesson_id=other_lesson)
        with self.assertRaises(ToolError):
            self.register(request_id='req-1', model_name='otro-modelo/otro')
        with self.assertRaises(ToolError):
            self.register(request_id='req-1', reply='Respuesta distinta con mismo request_id.')
        exercises = list(self.exercises)
        with self.assertRaises(ToolError):
            self.register(request_id='req-1', exercise_id=exercises[0])
        with self.assertRaises(ToolError):
            self.register(request_id='req-1', assessment={'status': 'with_help', 'gaps': ['nueva duda']})
        for kind in ('tutor_reply', 'chat_message'):
            self.assertEqual(len(self.kind_count(kind)), 1)

    def test_register_rolls_back_all_writes_on_midway_error(self):
        original = tutor_mcp.write_event

        def flaky(conn, kind, cid, lid, body, event_id):
            if kind == 'assessment':
                raise ValueError('fallo simulado a mitad de la transacción')
            return original(conn, kind, cid, lid, body, event_id)

        with mock.patch.object(tutor_mcp, 'write_event', flaky):
            with self.assertRaises(ToolError):
                self.register(request_id='req-atomica',
                              assessment={'status': 'pending', 'gaps': ['duda'], 'notebook': [
                                  {'kind': 'decision', 'text': 'Nota de cuaderno', 'quote': 'duda'}]})
        for kind in ('chat_message', 'tutor_reply', 'assessment', 'tutor_note'):
            self.assertEqual(self.kind_count(kind), [], 'La transacción debe dejar la base intacta si algo falla.')
        # Con la base vacía no hay identidad persistida: el reintento completa aunque cambie el texto.
        result = self.register(request_id='req-atomica')
        self.assertFalse(result['alreadyRegistered'])
        self.assertEqual(len(self.kind_count('tutor_reply')), 1)
        # ID ya committeado: reutilizarlo con otro texto/target/evaluación se rechaza y no escribe.
        before = self.kind_count('tutor_reply')
        with self.assertRaises(ToolError):
            self.register(request_id='req-atomica', question='Reutilizo el ID con otra pregunta.')
        with self.assertRaises(ToolError):
            self.register(request_id='req-atomica', assessment={'status': 'with_help', 'gaps': ['otra duda']})
        self.assertEqual(self.kind_count('tutor_reply'), before)

    def test_note_pending_brief_and_register_general(self):
        note = self.save_note(content='Texto personal del apunte general para conversar.')
        record = self.note_pending(note)
        self.assertEqual(record['status'], 'pending')
        self.assertEqual(record['channel'], 'mcp')
        listing = tutor_mcp.tutor_pending()
        pending = listing['notePendings'][0]
        self.assertEqual(pending['requestId'], 'note-req-1')
        self.assertEqual(pending['noteId'], note['id'])
        self.assertEqual(pending['context']['studentText'], 'Texto personal del apunte general para conversar.')
        self.assertEqual(pending['currentNoteRevision'], note['revision'])
        self.assertNotIn('sourcePages', pending['context'], 'El listado no debe volcar páginas completas.')
        brief = tutor_mcp.tutor_note_brief(request_id='note-req-1')
        self.assertEqual(brief['context']['context']['studentText'], note['content'])
        self.assertEqual(brief['noteRevisionChanged'], False)
        self.assertEqual(brief['pendingExchange']['status'], 'pending')
        self.assertIn('register_note_exchange', brief['noteContract'])
        self.assertEqual(brief['manifest']['tooLarge'], False)
        result = tutor_mcp.register_note_exchange(request_id='note-req-1', note_id=note['id'],
                                                  question=record['message'],
                                                  reply='Explico la idea según tu apunte; revisalo con la fuente.',
                                                  model_name='agente-test/modelo-nota',
                                                  context_hash=brief['contextHash'])
        self.assertFalse(result['alreadyRegistered'])
        self.assertTrue(result['contextHashVerified'])
        stored = self.note_records()['note-req-1']
        self.assertEqual(stored['status'], 'answered')
        self.assertEqual(stored['source'], 'external-mcp')
        self.assertEqual(stored['model'], 'agente-test/modelo-nota')
        self.assertEqual(stored['tutorContext']['provider'], 'external-mcp')
        self.assertNotIn('rawResponse', json.dumps(stored))
        self.assertEqual(stored['request'], record['request'], 'La consulta original no se sobrescribe.')
        # Idempotencia: repetir la misma respuesta no duplica ni cambia la marca temporal.
        again = tutor_mcp.register_note_exchange(request_id='note-req-1', note_id=note['id'],
                                                 question=record['message'],
                                                 reply='Explico la idea según tu apunte; revisalo con la fuente.',
                                                 model_name='agente-test/modelo-nota',
                                                 context_hash=brief['contextHash'])
        self.assertTrue(again['alreadyRegistered'])
        self.assertEqual(self.note_records()['note-req-1']['answeredAt'], stored['answeredAt'])
        # Otra respuesta, nota o texto con el mismo request_id se rechazan.
        for change in ({'reply': 'Otra respuesta distinta.'}, {'note_id': note['id'] + '-x'},
                       {'question': 'Otra pregunta.'}):
            args = {'request_id': 'note-req-1', 'note_id': note['id'], 'question': record['message'],
                    'reply': 'Explico la idea según tu apunte; revisalo con la fuente.',
                    'model_name': 'agente-test/modelo-nota'}
            args.update(change)
            with self.assertRaises(ToolError):
                tutor_mcp.register_note_exchange(**args)
        self.assertEqual(tutor_mcp.tutor_pending()['notePendings'], [])
        # Los intercambios de apuntes no tocan el historial de eventos de curso.
        self.assertEqual(server.snapshot()['events'], [])

    def test_note_assessment_never_acredits_domain(self):
        note = self.save_note()
        record = self.note_pending(note)
        with self.assertRaises(ToolError):
            tutor_mcp.register_note_exchange(request_id='note-req-1', note_id=note['id'], question=record['message'],
                                             reply='Respuesta.', model_name='agente-test/m',
                                             assessment={'status': 'independent'})
        with self.assertRaises(ToolError):
            tutor_mcp.register_note_exchange(request_id='note-req-1', note_id=note['id'], question=record['message'],
                                             reply='Respuesta.', model_name='agente-test/m',
                                             assessment={'criterionChecks': [{'criterion': 'x', 'result': 'met'}]})
        result = tutor_mcp.register_note_exchange(request_id='note-req-1', note_id=note['id'], question=record['message'],
                                                  reply='Respuesta con dudas abiertas.', model_name='agente-test/m',
                                                  assessment={'status': 'with_help', 'evidence': ['Consultó la página'],
                                                              'gaps': ['Falta repasar la sección 2']})
        self.assertFalse(result['alreadyRegistered'])
        stored = self.note_records()['note-req-1']
        self.assertEqual(stored['assessment']['status'], 'with_help')
        self.assertNotIn('criterionChecks', stored['assessment'])
        self.assertEqual(stored['helpProvided'], True)

    def test_note_pending_channel_api_cannot_be_taken_over(self):
        note = self.save_note()
        with server.library().connect() as conn:
            record = {'id': 'api-req-1', 'noteId': note['id'], 'createdAt': server.now(), 'message': 'duda',
                      'context': {'scope': 'general', 'noteRevision': note['revision']}, 'status': 'pending',
                      'reply': '', 'helpProvided': True, 'channel': 'api', 'request': {}}
            conn.execute('INSERT INTO note_tutor VALUES(?,?)', ('api-req-1', json.dumps(record, ensure_ascii=False)))
        listing = tutor_mcp.tutor_pending()
        self.assertEqual(listing['notePendings'], [])
        with self.assertRaises(ToolError):
            tutor_mcp.register_note_exchange(request_id='api-req-1', note_id=note['id'], question='duda',
                                             reply='Respuesta externa.', model_name='agente-test/m')
        stored = self.note_records()['api-req-1']
        self.assertEqual(stored['status'], 'pending')

    def test_note_flow_in_vault_without_courses(self):
        with server.connect() as con:
            con.execute('DELETE FROM events')
            con.execute('DELETE FROM courses')
        self.assertEqual(tutor_mcp.tutor_courses()['courses'], [])
        listing = tutor_mcp.tutor_pending()
        self.assertEqual(listing['coursesCount'], 0)
        note = self.save_note(content='Apunte de solo lectura sin ningún PDF asociado.')
        record = self.note_pending(note, request_id='note-req-2', message='Abrí esta duda con el apunte.')
        brief = tutor_mcp.tutor_note_brief(request_id='note-req-2')
        self.assertEqual(brief['context']['context']['studentText'], note['content'])
        result = tutor_mcp.register_note_exchange(request_id='note-req-2', note_id=note['id'],
                                                  question=record['message'], reply='Explicación del agente externo.',
                                                  model_name='agente-test/modelo', context_hash=brief['contextHash'])
        self.assertEqual(result['contextHashVerified'], True)
        self.assertEqual(self.note_records()['note-req-2']['status'], 'answered')

    def test_note_pdf_page_context_and_revision_guard(self):
        note = self.save_note(title='Apunte por página', shared=False, documentId='fixture-pdf', page=1,
                              writingScope='page', pageNotes={'fixture-pdf': {'1': 'Mi nota de la página 1'}})
        record = self.note_pending(note, request_id='note-req-3', message='Duda de la página 1.',
                                   scope='page', page=1)
        brief = tutor_mcp.tutor_note_brief(request_id='note-req-3')
        self.assertEqual(brief['context']['context']['documentId'], 'fixture-pdf')
        self.assertEqual(brief['context']['context']['page'], 1)
        self.assertEqual(brief['context']['context']['studentText'], 'Mi nota de la página 1')
        self.assertEqual(brief['context']['sourcePages'][0]['text'], 'PDF temporal pagina 1')
        result = tutor_mcp.register_note_exchange(request_id='note-req-3', note_id=note['id'],
                                                  question=record['message'], reply='Explicación de la página.',
                                                  model_name='agente-test/modelo', context_hash=brief['contextHash'])
        self.assertTrue(result['contextHashVerified'])
        self.assertFalse(result['noteRevisionChanged'])
        # Consulta nueva sobre el mismo apunte: la revisión esperada manda.
        record2 = self.note_pending(note, request_id='note-req-4', message='Consulta nueva.', scope='page', page=1)
        self.save_note(id=note['id'], title='Apunte por página', shared=False, documentId='fixture-pdf', page=1,
                       writingScope='page', pageNotes={'fixture-pdf': {'1': 'Mi nota de la página 1 editada'}},
                       revision=note['revision'])
        edited = next(n for n in server.snapshot()['library']['notes'] if n['id'] == note['id'])
        self.assertEqual(edited['revision'], note['revision'] + 1)
        with self.assertRaises(ToolError):
            tutor_mcp.register_note_exchange(request_id='note-req-4', note_id=note['id'], question=record2['message'],
                                             reply='x', model_name='agente-test/m', expected_note_revision=note['revision'])
        stale_brief = tutor_mcp.tutor_note_brief(request_id='note-req-4')
        self.assertTrue(stale_brief['noteRevisionChanged'], 'El brief debe avisar que el apunte cambió tras la consulta.')
        result = tutor_mcp.register_note_exchange(request_id='note-req-4', note_id=note['id'],
                                                  question=record2['message'], reply='Respuesta con material actual.',
                                                  model_name='agente-test/modelo', context_hash=brief['contextHash'])
        self.assertFalse(result['contextHashVerified'], 'El hash viejo no puede verificarse contra materiales nuevos.')
        self.assertEqual(result['noteRevisionChanged'], True)
        trace = self.note_records()['note-req-4']['tutorContext']
        self.assertEqual(trace['noteRevisionAtAnswer'], note['revision'] + 1)

    def test_note_brief_by_note_id_without_pending(self):
        note = self.save_note(content='Apunte libre para releer.')
        brief = tutor_mcp.tutor_note_brief(note_id=note['id'])
        self.assertEqual(brief['context']['context']['studentText'], note['content'])
        self.assertEqual(brief['pendingExchange'], None)
        self.assertIsNone(brief['pendingExchange'])
        with self.assertRaises(ToolError):
            tutor_mcp.tutor_note_brief(request_id='inexistente-req')
        with self.assertRaises(ToolError):
            tutor_mcp.tutor_note_brief()
        with self.assertRaises(ToolError):
            tutor_mcp.tutor_note_brief(request_id='a', note_id='b')

    def test_pliegos_tools(self):
        listing = tutor_mcp.list_pliegos()
        self.assertIn({'id': 'local', 'title': 'Pliego local'}, listing['rooms'])
        opened = tutor_mcp.open_pliego(room_id='local')
        self.assertEqual(opened['id'], 'local')
        with self.assertRaises(ToolError):
            tutor_mcp.open_pliego(room_id='pliego-inexistente')


if __name__ == '__main__':
    unittest.main()
