"""Highlight colors and soft removal, on a disposable database and fixture course.

Covers the additive /api/annotation actions 'recolor' and 'remove': both keep the
original event and append a revision, so nothing in the study history is erased.
No model calls; no real course or student history is touched.
"""
import json
import re
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
sys.path.insert(0, str(Path(__file__).resolve().parent / 'helpers'))
from fixture_workspace import build


class HighlightColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='highlight-color-tests-')
        cls.old_db, cls.old_data, cls.old_port, cls.old_root = server.DB, server.DATA, server.PORT, server.ROOT
        server.ROOT = build(Path(cls.tmp.name) / 'fixture-root')
        server.DATA = Path(cls.tmp.name)
        server.DB = Path(cls.tmp.name) / 'test.sqlite3'
        server.KEY = ''
        server.init_db()
        cls.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        server.PORT = cls.http.server_address[1]
        cls.base = 'http://127.0.0.1:' + str(server.PORT)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown(); cls.http.server_close(); cls.tmp.cleanup()
        server.DB, server.DATA, server.PORT, server.ROOT = cls.old_db, cls.old_data, cls.old_port, cls.old_root

    def setUp(self):
        with server.connect() as c:
            c.execute('DELETE FROM events')
            c.execute('DELETE FROM courses')
            c.execute('DELETE FROM annotation_revisions')
            c.execute('UPDATE config SET body=? WHERE id=1', (json.dumps(server.BASE_SETTINGS),))
        server.init_db()
        self.course = server.snapshot()['courses'][0]
        self.cid = self.course['id']
        self.lid = self.course['lessons'][0]['id']
        self.block = self.course['lessons'][0]['blocks'][0]

    def post(self, path, data):
        req = Request(self.base + path, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
        with urlopen(req) as r: return json.load(r)

    def get(self, path):
        with urlopen(self.base + path) as r: return json.load(r)

    def create_highlight(self, event_id='highlight-1', color='yellow'):
        text = self.block['text']
        match = re.search(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]{5,25}', text)
        quote = match.group(0)
        payload = {'blockId': self.block['id'], 'quote': quote, 'start': match.start(), 'end': match.end(),
                   'type': 'highlight', 'highlight': True, 'color': color, 'comment': '', 'shareWithTutor': False}
        self.post('/api/event', {'id': event_id, 'kind': 'annotation', 'courseId': self.cid, 'lessonId': self.lid, 'data': payload})
        return next(e for e in self.get('/api/state')['events'] if e['id'] == event_id)

    def test_recolor_changes_color_and_preserves_original_and_quote(self):
        event = self.create_highlight()
        self.assertEqual(event['data']['color'], 'yellow')
        result = self.post('/api/annotation', {'action': 'recolor', 'id': event['id'], 'color': 'blue', 'expectedRevision': 0})
        self.assertTrue(result['ok'])
        state = self.get('/api/state')
        saved = next(e for e in state['events'] if e['id'] == event['id'])
        self.assertEqual(saved['data']['color'], 'blue')
        self.assertEqual(saved['data']['quote'], event['data']['quote'])
        self.assertEqual(saved['data']['comment'], '')
        self.assertEqual(saved['data']['annotationRevision'], 1)
        self.assertEqual(state['annotationRevisions'], [event])

    def test_recolor_rejects_unknown_color_and_stale_revision(self):
        event = self.create_highlight()
        with self.assertRaises(HTTPError) as unknown:
            self.post('/api/annotation', {'action': 'recolor', 'id': event['id'], 'color': 'chartreuse', 'expectedRevision': 0})
        self.assertEqual(unknown.exception.code, 400)
        self.post('/api/annotation', {'action': 'recolor', 'id': event['id'], 'color': 'green', 'expectedRevision': 0})
        with self.assertRaises(HTTPError) as stale:
            self.post('/api/annotation', {'action': 'recolor', 'id': event['id'], 'color': 'pink', 'expectedRevision': 0})
        self.assertEqual(stale.exception.code, 400)
        saved = next(e for e in self.get('/api/state')['events'] if e['id'] == event['id'])
        self.assertEqual(saved['data']['color'], 'green')

    def test_soft_remove_keeps_event_revision_and_original_quote(self):
        event = self.create_highlight('highlight-remove')
        result = self.post('/api/annotation', {'action': 'remove', 'id': event['id'], 'expectedRevision': 0})
        self.assertTrue(result['ok'])
        state = self.get('/api/state')
        saved = next((e for e in state['events'] if e['id'] == event['id']), None)
        self.assertIsNotNone(saved, 'the annotation event must remain for the history')
        self.assertTrue(saved['data']['removed'])
        self.assertEqual(saved['data']['quote'], event['data']['quote'])
        self.assertEqual(saved['data']['annotationRevision'], 1)
        self.assertEqual(state['annotationRevisions'], [event])

    def test_editing_a_highlight_keeps_its_marker_and_color(self):
        event = self.create_highlight('highlight-note', color='pink')
        self.post('/api/annotation', {'action': 'edit', 'id': event['id'], 'comment': 'Una duda sobre este fragmento.',
                                      'type': 'personal', 'shareWithTutor': True, 'expectedRevision': 0})
        saved = next(e for e in self.get('/api/state')['events'] if e['id'] == event['id'])
        self.assertEqual(saved['data']['comment'], 'Una duda sobre este fragmento.')
        self.assertTrue(saved['data'].get('highlight'))
        self.assertEqual(saved['data']['color'], 'pink')
        self.assertEqual(saved['data']['annotationRevision'], 1)

    def test_removed_highlight_leaves_automatic_context_but_stays_in_history(self):
        event = self.create_highlight('highlight-shared')
        self.post('/api/annotation', {'action': 'edit', 'id': event['id'], 'comment': 'Una duda compartida.',
                                      'type': 'doubt', 'shareWithTutor': True, 'expectedRevision': 0})
        target = {'kind': 'study', 'courseId': self.cid, 'lessonId': self.lid}
        state = self.get('/api/state')
        self.assertIn(event['id'], server.tutor_context.defaults(state, target)['annotationIds'])
        self.post('/api/annotation', {'action': 'remove', 'id': event['id'], 'expectedRevision': 1})
        state = self.get('/api/state')
        # The retired highlight leaves the automatic selection...
        self.assertNotIn(event['id'], server.tutor_context.defaults(state, target)['annotationIds'])
        # ...and is skipped even when an older explicit selection still names it.
        selection = {**server.tutor_context.defaults(state, target), 'annotationIds': [event['id']]}
        built = server.tutor_context.build(server.library(), state, target, selection, '¿Qué significa?')
        self.assertEqual(built['payload']['annotations'], [])
        self.assertEqual(built['payload']['openDoubts'], [])
        self.assertTrue(any('quitadas del resaltado' in w for w in built['manifest']['warnings']))
        # The full record keeps the quote and the revision for export.
        recorded = next(e for e in state['events'] if e['id'] == event['id'])
        self.assertTrue(recorded['data']['removed'])
        self.assertEqual(recorded['data']['quote'], event['data']['quote'])
        # Two revisions survive: the shared edit and the state before removal.
        self.assertEqual(len(state['annotationRevisions']), 2)
        self.assertTrue(state['annotationRevisions'][-1]['data']['shareWithTutor'])

    def test_note_tutor_mcp_channel_stays_pending_and_calls_no_provider(self):
        with server.connect() as c:
            c.execute('DELETE FROM note_tutor')
            c.execute('DELETE FROM notes')
        note = server.library().save_note({'title': 'Apunte MCP', 'folder': '', 'content': 'Contenido propio.',
                                           'shared': False, 'documentId': None, 'page': None, 'anchors': []})
        question = {'requestId': 'mcp-pending-1', 'noteId': note['id'], 'noteRevision': note['revision'],
                    'message': '¿Qué relación hay?', 'scope': 'general', 'channel': 'mcp'}
        with patch.object(server, 'openrouter', side_effect=AssertionError('the MCP channel must not call a provider')):
            record = self.post('/api/note-tutor', question)
            again = self.post('/api/note-tutor', question)
        self.assertEqual(record['status'], 'pending')
        self.assertEqual(record['channel'], 'mcp')
        self.assertEqual(record['reply'], '')
        self.assertTrue(record['helpProvided'])
        self.assertEqual(again['id'], record['id'])
        stored = [q for q in self.get('/api/state')['library']['noteTutor'] if q['id'] == record['id']]
        self.assertEqual(len(stored), 1, 'a repeated MCP question must not duplicate the pending record')
        self.assertNotIn('rawResponse', stored[0])

    def test_note_tutor_rejects_unknown_channel(self):
        with self.assertRaises(HTTPError) as bad:
            self.post('/api/note-tutor', {'requestId': 'bad-channel', 'noteId': 'n', 'message': 'hola', 'channel': 'telepathy'})
        self.assertEqual(bad.exception.code, 400)


if __name__ == '__main__':
    unittest.main()
