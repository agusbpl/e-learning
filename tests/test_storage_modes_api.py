"""API de almacenamiento con alias local y de modos del tutor; bases desechables.

Cubre el hook del integrador en server.py:
- alias local (`local-migrated.json`): con marcador válido, `active_workspace`,
  `connect` y `library` abren la bóveda nueva conservando el id 'local'; con
  marcador inválido nunca hay fallback silencioso a la base vieja; sin marcador
  se mantiene el respaldo legítimo DB/DATA/ROOT que parchan las pruebas viejas.
- `POST /api/tutor-modes`: acciones exactas del contrato/UI.
- política de modo ANTES de generar: se captura el mensaje de sistema con un
  mock (sin llamar a ningún proveedor) y se verifica el `mode_prompt` y la
  puerta de evidencia.
- payload real de `tutor_modes.export_payload/import_payload` en `snapshot()` y
  `POST /api/restore`.

Nunca se usa el `~/Margen` real ni HOME real: todo vive en temporales y el
Margen se fija por `GLOSA_MARGEN_DIR` por prueba. La validez semántica del tutor
no se prueba acá (ver docs/evaluacion-rigurosa.md).
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests' / 'helpers'))

from fixture_workspace import build  # noqa: E402

import calendar_store  # noqa: E402
import rooms  # noqa: E402
import server  # noqa: E402
import tutor_modes  # noqa: E402


def course_body(course_id='c1', lessons=(('c1-l1', 'Lección 1', 60),)):
    return {'id': course_id, 'title': 'Materia ' + course_id, 'version': '2026-10-01',
            'lessons': [{'id': lid, 'title': title, 'minutes': minutes, 'priority': index,
                         'prerequisites': [], 'blocks': [], 'exercises': []}
                        for index, (lid, title, minutes) in enumerate(lessons, 1)]}


class StorageModesApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._saved_env = {key: os.environ.get(key) for key in ('LEARNING_DATA_DIR', 'GLOSA_MARGEN_DIR', 'HOME')}
        cls.tmp = tempfile.TemporaryDirectory(prefix='glosa-modes-api-')
        base = Path(cls.tmp.name)
        (base / 'home').mkdir()
        (base / 'margen').mkdir()
        os.environ['HOME'] = str(base / 'home')
        os.environ['LEARNING_DATA_DIR'] = str(base / 'data')
        os.environ['GLOSA_MARGEN_DIR'] = str(base / 'margen')
        (base / 'data').mkdir()
        cls.old = (server.ROOT, server.DATA, server.DB, server.KEY, server.PORT)
        server.ROOT = build(base / 'fixture-root')
        server.DATA = base / 'data'
        server.DB = base / 'data' / 'test.sqlite3'
        server.KEY = ''
        server.init_db()
        cls.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        server.PORT = cls.http.server_address[1]
        cls.base = 'http://127.0.0.1:' + str(server.PORT)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join(timeout=2)
        server.ROOT, server.DATA, server.DB, server.KEY, server.PORT = cls.old
        for key, value in cls._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        cls.tmp.cleanup()

    def setUp(self):
        # Margen aislado por prueba: preferencia/temarios/plan no se comparten.
        self.margen = Path(self.tmp.name) / ('margen-' + uuid.uuid4().hex)
        self.margen.mkdir()
        self._previous_margen = os.environ.get('GLOSA_MARGEN_DIR')
        os.environ['GLOSA_MARGEN_DIR'] = str(self.margen)

        def restore_margen():
            if self._previous_margen is None:
                os.environ.pop('GLOSA_MARGEN_DIR', None)
            else:
                os.environ['GLOSA_MARGEN_DIR'] = self._previous_margen
            shutil.rmtree(self.margen, ignore_errors=True)

        self.addCleanup(restore_margen)
        # Biblioteca local legible y estable entre pruebas (solo base temporal).
        # Los apuntes son archivos: hay que retirarlos o el índice los readopta.
        for folder in ('Apuntes', 'notes'):
            shutil.rmtree(server.DATA / folder, ignore_errors=True)
        with server.connect() as conn:
            tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            for table in tables:
                if table != 'config':
                    conn.execute('DELETE FROM ' + table)
            conn.execute('UPDATE config SET body=? WHERE id=1', (json.dumps(server.BASE_SETTINGS),))
        server.init_db()

    # ---------------------------------------------------------------- helpers

    def post(self, path, data, room=None):
        headers = {'Content-Type': 'application/json'}
        if room:
            headers['X-Glosa-Room'] = room
        req = Request(self.base + path, data=json.dumps(data).encode(), headers=headers)
        with urlopen(req, timeout=10) as response:
            return json.load(response)

    def get(self, path, room=None):
        headers = {'X-Glosa-Room': room} if room else {}
        with urlopen(Request(self.base + path, headers=headers), timeout=10) as response:
            return json.load(response)

    def raw_get(self, path):
        with urlopen(Request(self.base + path), timeout=10) as response:
            return response.status, response.read().decode('utf-8')

    def pliego(self, title):
        return rooms.create(server.DATA, server.ROOT, title)['id']

    def add_course(self, room_id, body, calendar=()):
        scope = rooms.room(server.DATA, server.ROOT, room_id)
        with tutor_modes._Scoped(server, scope), server.connect() as conn:
            conn.execute('INSERT OR REPLACE INTO courses VALUES(?,?)', (body['id'], json.dumps(body, ensure_ascii=False)))
            for event in calendar:
                conn.execute('INSERT OR REPLACE INTO calendar_events VALUES(?,?)',
                             (event['id'], json.dumps(event, ensure_ascii=False)))
        return scope

    def local_course(self):
        course = server.snapshot()['courses'][0]
        return course['id'], course['lessons'][0]['id']

    # ------------------------------------------------------- tutor modes API

    def test_overview_and_preference_actions_are_the_ui_contract(self):
        overview = self.post('/api/tutor-modes', {'action': 'overview'})
        self.assertEqual(overview['policyVersion'], tutor_modes.POLICY_VERSION)
        self.assertIn(overview['effective']['decision']['effectiveMode'], tutor_modes.MODES)
        self.assertIn('choice', overview['preference'])

        manual = self.post('/api/tutor-modes', {'action': 'setPreference', 'choice': 'manual', 'mode': 'extreme'})
        self.assertEqual(manual['preference']['choice'], 'manual')
        self.assertEqual(manual['preference']['mode'], 'extreme')
        self.assertEqual(manual['effective']['decision']['effectiveMode'], 'extreme')
        self.assertTrue(manual['effective']['decision']['overrideActive'])

        auto = self.post('/api/tutor-modes', {'action': 'setPreference', 'choice': 'auto', 'mode': ''})
        self.assertEqual(auto['preference']['choice'], 'auto')
        self.assertIsNone(auto['preference']['mode'])
        self.assertIn(auto['effective']['decision']['effectiveMode'], tutor_modes.MODES)

    def test_overview_includes_global_plan_not_only_the_plan_action(self):
        """El panel monta con overview y espera `plan`; no debe depender de la acción plan.

        Compromisos reales de un pliego temporal: el overview (una sola llamada,
        como hace web/tutor-modes.js) ya trae `plan.exams`/`plan.rooms` con las
        señales que la UI usa para mostrar y reordenar la prioridad.
        """
        room = self.pliego('Overview')
        today = server.datetime.now(server.LOCAL_ZONE).date().isoformat()
        self.add_course(room, course_body('c1', lessons=(('c1-l1', 'Uno', 30),)), calendar=[
            calendar_store.validate({'id': 'ev1', 'courseId': 'c1', 'title': 'Parcial',
                                     'date': today, 'kind': 'exam', 'revision': 1})])
        target = '|'.join((room, 'c1', 'ev1'))

        overview = self.post('/api/tutor-modes', {'action': 'overview'})
        self.assertEqual(overview['policyVersion'], tutor_modes.POLICY_VERSION)
        self.assertIn('plan', overview, 'overview debe incluir el plan global que consume la UI')
        self.assertEqual(overview['plan']['rooms'].get(room), 'Overview')
        entry = next((e for e in overview['plan']['exams'] if e['target'] == target), None)
        self.assertIsNotNone(entry, 'el compromiso real del pliego temporal debe aparecer en overview')
        self.assertEqual(entry['kind'], 'exam')
        self.assertEqual(entry['date'], today)
        # Señales que la UI de plan usa: reordenar y ver asignación real de minutos.
        self.assertIn('priorityReasons', entry)
        self.assertIn('plan', entry)
        self.assertIn('minutesAllocated', entry)
        # overview y la acción `plan` comparten el mismo contrato de plan global.
        plan_action = self.post('/api/tutor-modes', {'action': 'plan'})['plan']
        self.assertEqual([e['target'] for e in overview['plan']['exams']],
                         [e['target'] for e in plan_action['exams']])
        # La preferencia sigue siendo parte del contrato del panel.
        self.assertIn('choice', overview['preference'])

    def test_plan_and_set_plan_edits_use_composite_targets(self):
        room = self.pliego('Plan')
        self.add_course(room, course_body('c1'), calendar=[
            calendar_store.validate({'id': 'ev1', 'courseId': 'c1', 'title': 'Parcial',
                                     'date': server.datetime.now(server.LOCAL_ZONE).date().isoformat(),
                                     'kind': 'exam', 'revision': 1}),
            calendar_store.validate({'id': 'ev2', 'courseId': 'c1', 'title': 'TP',
                                     'date': server.datetime.now(server.LOCAL_ZONE).date().isoformat(),
                                     'kind': 'deadline', 'revision': 1})])
        target_a = '|'.join((room, 'c1', 'ev1'))
        target_b = '|'.join((room, 'c1', 'ev2'))
        plan = self.post('/api/tutor-modes', {'action': 'plan'})['plan']
        targets = {entry['target'] for entry in plan['exams']}
        self.assertIn(target_a, targets)
        self.assertIn(target_b, targets)

        edited = self.post('/api/tutor-modes', {'action': 'setPlanEdits', 'edits': [target_b, target_a]})
        self.assertTrue(edited['edited'])
        self.assertEqual(edited['plan']['exams'][0]['target'], target_b)
        self.assertEqual(tutor_modes.read_plan_edits(server), [target_b, target_a])

    def test_confirm_topic_and_ack_notice_actions(self):
        room = self.pliego('Temario')
        self.add_course(room, course_body('c1', lessons=(('c1-l1', 'Uno', 30), ('c1-l2', 'Dos', 30))))
        tutor_modes.save_exam_topics(server, room, 'c1', 'ev1', ['c1-l1'], status='proposed')
        confirmed = self.post('/api/tutor-modes', {'action': 'confirmTopic', 'roomId': room,
                                                   'courseId': 'c1', 'eventId': 'ev1', 'expectedRevision': 1})
        self.assertEqual(confirmed['topics']['status'], 'confirmed')
        self.assertEqual(confirmed['topics']['confirmedBy'], 'student')

        state = tutor_modes.read_state(server)
        state['notice'] = {'from': 'extreme', 'to': 'flexible', 'reasons': ['prueba'],
                           'at': '2026-10-16', 'delivered': False}
        tutor_modes.write_state(server, state)
        ack = self.post('/api/tutor-modes', {'action': 'ackNotice'})
        self.assertTrue(ack['acknowledged'])
        self.assertTrue(tutor_modes.read_state(server)['notice']['delivered'])

    def test_unknown_action_is_a_client_error(self):
        with self.assertRaises(HTTPError) as caught:
            self.post('/api/tutor-modes', {'action': 'no-existe'})
        self.assertEqual(caught.exception.code, 400)
        caught.exception.close()

    def test_static_tutor_modes_assets_are_served_and_wired(self):
        status, css = self.raw_get('/tutor-modes.css')
        self.assertEqual(status, 200)
        self.assertIn('tutor-modes-panel', css)
        status, js = self.raw_get('/tutor-modes.js')
        self.assertEqual(status, 200)
        self.assertIn('window.TutorModes', js)
        status, index = self.raw_get('/')
        self.assertEqual(status, 200)
        self.assertIn('<link rel="stylesheet" href="/tutor-modes.css">', index)
        self.assertIn('<script src="/tutor-modes.js" defer></script>', index)
        # Orden exigido por el contrato: tutor-modes.js antes de plan.js.
        self.assertLess(index.index('tutor-modes.js'), index.index('/plan.js'))

    def test_mode_prompt_precedes_generation_and_gate_is_reported(self):
        cid, lid = self.local_course()
        today = server.datetime.now(server.LOCAL_ZONE).date().isoformat()
        event = calendar_store.validate({'id': 'near-exam', 'courseId': cid, 'title': 'Parcial cercano',
                                         'date': today, 'kind': 'exam', 'revision': 1})
        with server.connect() as conn:
            conn.execute('INSERT OR REPLACE INTO calendar_events VALUES(?,?)', (event['id'], json.dumps(event)))
        tutor_modes.save_preference(server, {'choice': 'auto'})

        captured = {}

        def fake_completion(settings, messages, *, structured=False):
            captured['messages'] = messages
            reply = {'reply': 'Bien planteado.', 'status': 'pending', 'evidence': [], 'gaps': [],
                     'nextAction': 'continue', 'reason': 'Prueba sin proveedor.', 'followUp': ''}
            return {'choices': [{'message': {'content': json.dumps(reply)}, 'finish_reason': 'stop'}], 'model': 'mock'}

        with patch.object(server, 'tutor_completion', side_effect=fake_completion):
            result = self.post('/api/tutor', {'courseId': cid, 'lessonId': lid, 'message': '¿Cómo lo razono?'})

        self.assertIn('messages', captured, 'el tutor no debe llamar a ningún proveedor real')
        system_message = captured['messages'][0]
        self.assertEqual(system_message['role'], 'system')
        self.assertEqual(captured['messages'][1]['role'], 'user')
        self.assertTrue(system_message['content'].startswith(server.TUTOR_POLICY))
        self.assertIn(tutor_modes.mode_prompt('flexible'), system_message['content'])
        self.assertEqual(result['tutorMode']['mode'], 'flexible')
        self.assertEqual(result['tutorMode']['version'], tutor_modes.POLICY_VERSION)
        self.assertIn(tutor_modes.GATE_CLAUSE, result['tutorMode']['never'])
        self.assertEqual(result['tutorContext']['effectiveMode'], 'flexible')

    def test_note_tutor_uses_mode_prompt_before_provider(self):
        note = server.library().save_note({'title': 'Apunte', 'folder': '', 'content': 'Texto',
                                           'shared': True, 'documentId': None, 'page': None, 'anchors': []})
        captured = {}

        def fake_completion(settings, messages, *, structured=False):
            captured['messages'] = messages
            return {'choices': [{'message': {'content': 'Explicación breve.'}, 'finish_reason': 'stop'}], 'model': 'mock'}

        with patch.object(server, 'tutor_completion', side_effect=fake_completion):
            result = self.post('/api/note-tutor', {'requestId': 'req-modes-1', 'message': '¿Qué es?',
                                                   'noteId': note['id'], 'noteRevision': note['revision'],
                                                   'scope': 'general'})
        self.assertIn('messages', captured)
        self.assertTrue(captured['messages'][0]['content'].startswith(server.NOTE_TUTOR_POLICY))
        self.assertIn('Modo', captured['messages'][0]['content'])
        self.assertEqual(result['status'], 'answered')
        self.assertIn(result['tutorMode']['mode'], tutor_modes.MODES)

    # --------------------------------------------- payload backup / restore

    def test_snapshot_exports_real_modes_payload(self):
        self.post('/api/tutor-modes', {'action': 'setPreference', 'choice': 'manual', 'mode': 'strict'})
        state = self.get('/api/state')
        self.assertIn('tutorModes', state)
        self.assertEqual(state['tutorModes']['format'], tutor_modes.FORMAT)
        self.assertEqual(state['tutorModes']['policyVersion'], tutor_modes.POLICY_VERSION)
        self.assertEqual(state['tutorModes']['preference']['mode'], 'strict')

    def test_restore_imports_modes_payload_and_rejects_invalid(self):
        self.post('/api/tutor-modes', {'action': 'setPreference', 'choice': 'manual', 'mode': 'strict'})
        state = self.get('/api/state')
        state['tutorModes'] = {**state['tutorModes'],
                               'preference': {'choice': 'manual', 'mode': 'extreme', 'updatedAt': '2026-10-16'}}
        self.post('/api/restore', state)
        after = self.get('/api/state')
        self.assertEqual(after['tutorModes']['preference']['mode'], 'extreme')

        invalid = {'schemaVersion': 1, 'courses': [], 'events': [], 'tutorModes': {'format': 'ajeno'}}
        with self.assertRaises(HTTPError) as caught:
            self.post('/api/restore', invalid)
        self.assertEqual(caught.exception.code, 400)
        caught.exception.close()
        self.assertEqual(tutor_modes.read_preference(server)['mode'], 'extreme')

    # ------------------------------------------------------- local alias

    def _vault(self):
        vault = Path(self.tmp.name) / ('vault-' + uuid.uuid4().hex)
        (vault / 'learning').mkdir(parents=True)
        (vault / 'assets').mkdir()
        (vault / 'pliego.json').write_text(json.dumps(
            {'format': 'glosa-pliego', 'version': 1, 'id': 'local', 'title': 'Biblioteca local'}))
        # Inicializa una bóveda completa (server.init_db) con su propio scope.
        scope = {'id': 'local', 'title': 'Biblioteca local', 'kind': 'local-alias',
                 'path': str(vault), 'data': vault / 'learning', 'root': vault / 'assets'}
        token = server.ACTIVE_WORKSPACE.set(scope)
        try:
            server.init_db()
        finally:
            server.ACTIVE_WORKSPACE.reset(token)
        from library import Library
        lib = Library(vault / 'learning' / 'learning.sqlite3', vault / 'learning', vault / 'assets')
        return vault, lib

    def _write_marker(self, vault, **overrides):
        info = {'format': 'glosa-local-alias', 'version': 1, 'id': 'local', 'path': str(vault)}
        info.update(overrides)
        marker = Path(server.DATA) / 'local-migrated.json'
        marker.write_text(json.dumps(info))
        self.addCleanup(lambda: marker.unlink(missing_ok=True))
        return marker

    def test_without_alias_local_keeps_the_legitimate_legacy_fallback(self):
        self.assertIsNone(server.local_alias())
        workspace = server.active_workspace()
        self.assertEqual(workspace['id'], 'local')
        self.assertIsNone(workspace.get('kind'))
        self.assertEqual(Path(workspace['data']), Path(server.DATA))
        self.assertEqual(server.library().db, Path(server.DB))

    def test_valid_alias_routes_library_and_db_to_the_new_vault(self):
        vault, lib = self._vault()
        marker_event = {'id': 'vault-only', 'courseId': 'x', 'title': 'Marca de bóveda',
                        'date': '2026-12-01', 'kind': 'theory', 'revision': 1}
        with lib.connect() as conn:
            conn.execute('INSERT INTO calendar_events VALUES(?,?)', (marker_event['id'], json.dumps(marker_event)))
        self._write_marker(vault)

        workspace = server.active_workspace()
        self.assertEqual(workspace['id'], 'local')
        self.assertEqual(workspace['kind'], 'local-alias')
        self.assertEqual(Path(workspace['path']), vault)
        self.assertEqual(server.library().data, vault / 'learning')
        self.assertEqual(server.library().db, vault / 'learning' / 'learning.sqlite3')
        with server.connect() as conn:
            ids = {row['id'] for row in conn.execute('SELECT id FROM calendar_events')}
        self.assertIn('vault-only', ids)
        # La API local también resuelve el alias, conservando el id 'local'.
        state = self.get('/api/state')
        self.assertEqual(state['room']['id'], 'local')
        self.assertEqual(state['room']['title'], 'Biblioteca local')
        self.assertIn('vault-only', {event['id'] for event in state['calendarEvents']})

    def test_invalid_marker_never_silently_opens_the_old_database(self):
        marker = Path(server.DATA) / 'local-migrated.json'
        marker.write_text(json.dumps({'format': 'glosa-local-alias', 'version': 1, 'id': 'local',
                                      'path': str(Path(self.tmp.name) / 'no-existe')}))
        self.addCleanup(lambda: marker.unlink(missing_ok=True))
        with self.assertRaises(ValueError):
            server.active_workspace()
        with self.assertRaises(ValueError):
            server.library()
        with self.assertRaises(HTTPError) as caught:
            self.get('/api/state')
        self.assertEqual(caught.exception.code, 400)
        caught.exception.close()


if __name__ == '__main__':
    unittest.main()
