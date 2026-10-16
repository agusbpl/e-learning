"""Integración de los MCP de autoría y tutor con modos/plan global; base temporal.

Solo lectura/escritura en el fixture: nunca toca el ~/Margen real, HOME ni
proveedores. Sin runtime MCP disponible, el módulo se saltea (correr con
.venv-author/bin/python). La validez semántica del tutor NO se prueba acá.

El aislamiento de entorno se hace en setUpClass (no al importar) para no
contaminar el proceso de otras suites que corran en la misma invocación.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests' / 'helpers'))

HAS_MCP = importlib.util.find_spec('mcp') is not None
NEEDS_MCP = unittest.skipUnless(HAS_MCP, 'mcp no disponible: correr con .venv-author/bin/python')


def course_body(course_id='c1'):
    return {'id': course_id, 'title': 'Materia ' + course_id, 'version': '2026-10-01', 'lessons': [
        {'id': course_id + '-l1', 'title': 'Lección 1', 'minutes': 60, 'priority': 1, 'prerequisites': [],
         'blocks': [], 'exercises': []},
        {'id': course_id + '-l2', 'title': 'Lección 2', 'minutes': 45, 'priority': 2, 'prerequisites': [],
         'blocks': [], 'exercises': []}]}


@NEEDS_MCP
class ModesMcpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from mcp.server.mcpserver.exceptions import ToolError
        from fixture_workspace import build
        import calendar_store
        import rooms
        import server
        import tutor_modes

        cls._saved = {key: os.environ.get(key) for key in ('LEARNING_DATA_DIR', 'GLOSA_MARGEN_DIR', 'HOME')}
        cls._tmp = Path(tempfile.mkdtemp(prefix='glosa-modes-mcp-'))
        (cls._tmp / 'home').mkdir()
        os.environ['LEARNING_DATA_DIR'] = str(cls._tmp)
        os.environ['GLOSA_MARGEN_DIR'] = str(cls._tmp / 'margen')
        os.environ['HOME'] = str(cls._tmp / 'home')

        cls.old = server.DATA, server.ROOT, server.DB, server.KEY
        server.ROOT = build(cls._tmp / 'fixture-root')
        server.DATA = cls._tmp
        server.DB = cls._tmp / 'test.sqlite3'
        server.KEY = ''
        server.init_db()

        import author_mcp
        import tutor_mcp

        cls.server, cls.rooms, cls.calendar_store = server, rooms, calendar_store
        cls.tutor_modes, cls.author_mcp, cls.tutor_mcp, cls.ToolError = tutor_modes, author_mcp, tutor_mcp, ToolError
        created = rooms.create(server.DATA, server.ROOT, 'Modos')
        cls.room_id = created['id']
        cls.scope = rooms.room(server.DATA, server.ROOT, cls.room_id)
        with author_mcp._scoped(cls.scope), server.connect() as conn:
            conn.execute('INSERT OR REPLACE INTO courses VALUES(?,?)', ('c1', json.dumps(course_body(), ensure_ascii=False)))
            event = calendar_store.validate({'id': 'ev1', 'courseId': 'c1', 'title': 'Parcial',
                                             'date': '2026-12-01', 'kind': 'exam', 'revision': 1})
            conn.execute('INSERT OR REPLACE INTO calendar_events VALUES(?,?)', ('ev1', json.dumps(event, ensure_ascii=False)))

    @classmethod
    def tearDownClass(cls):
        cls.server.DATA, cls.server.ROOT, cls.server.DB, cls.server.KEY = cls.old
        for key, value in cls._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_author_proposes_topics_and_tutor_confirms_them(self):
        proposed = self.author_mcp.propose_exam_topics(self.room_id, 'c1', 'ev1', ['c1-l1'], rationale='Apunte y lección 1')
        self.assertEqual(proposed['status'], 'proposed')
        self.assertEqual(proposed['revision'], 1)
        with self.assertRaises(self.ToolError):
            self.author_mcp.propose_exam_topics(self.room_id, 'c1', 'ev1', ['inexistente'])
        confirmed = self.tutor_mcp.confirm_exam_topic(self.room_id, 'c1', 'ev1', expected_revision=1)
        self.assertEqual(confirmed['topics']['status'], 'confirmed')

    def test_global_plan_spans_all_pliegos(self):
        plan = self.tutor_mcp.global_study_plan()['plan']
        targets = [entry['target'] for entry in plan['exams']]
        self.assertIn('|'.join((self.room_id, 'c1', 'ev1')), targets)
        self.assertEqual([e for e in plan['exams'] if e['eventId'] == 'ev1'][0]['temario']['source'], 'confirmed')
        overview = self.author_mcp.global_courses_overview()
        self.assertIn(self.room_id, {pliego['roomId'] for pliego in overview['pliegos']})
        self.assertTrue(self.author_mcp.all_room_events()['events'])

    def test_tutor_mode_overview_and_manual_override(self):
        overview = self.tutor_mcp.tutor_mode_overview()
        self.assertEqual(overview['policyVersion'], self.tutor_modes.POLICY_VERSION)
        self.assertIn(self.tutor_modes.GATE_CLAUSE, overview['requirements']['never'])
        self.assertIn('Modo', overview['instructions'])
        manual = self.tutor_mcp.tutor_set_mode('manual', 'extreme')
        self.assertEqual(manual['effective']['effectiveMode'], 'extreme')
        self.assertEqual(manual['preference']['choice'], 'manual')
        auto = self.tutor_mcp.tutor_set_mode('auto')
        self.assertEqual(auto['preference']['choice'], 'auto')
        self.assertIn(auto['effective']['effectiveMode'], self.tutor_modes.MODES)

    def test_mode_block_precedes_generation_and_stamp_is_recorded(self):
        block = self.tutor_mcp.mode_block()
        self.assertIn('instructions', block)
        self.assertIn('evidenceRequirements', block['requirements'])
        stamp = self.tutor_mcp.mode_stamp()
        self.assertIn('effectiveMode', stamp)
        self.assertEqual(stamp['policyVersion'], self.tutor_modes.POLICY_VERSION)

    def test_author_brief_carries_mode_and_does_not_consume_the_notice(self):
        state = self.tutor_modes.read_state(self.server)
        state['preference'] = {'choice': 'auto', 'mode': None, 'updatedAt': '2026-10-16'}
        state['lastEffectiveMode'] = 'extreme'
        self.tutor_modes.write_state(self.server, state)
        brief = self.author_mcp.author_brief()
        self.assertIn('Modo', brief['tutorMode']['instructions'])
        self.assertEqual(brief['tutorMode']['policyVersion'], self.tutor_modes.POLICY_VERSION)
        self.assertIsNotNone(brief['tutorMode']['notice'])
        # El brief de autoría NO gasta la entrega: el canal del alumno todavía la ve una vez.
        first = self.tutor_mcp.tutor_mode_overview()
        self.assertIsNotNone(first['notice'])
        self.assertIsNone(self.tutor_mcp.tutor_mode_overview()['notice'])


if __name__ == '__main__':
    unittest.main()
