import tempfile
import json
import unittest
from pathlib import Path

from library import Library, note_markdown


class NoteMarkdownTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='glosa-note-markdown-')
        self.addCleanup(self.tmp.cleanup)
        self.data = Path(self.tmp.name)
        self.lib = Library(self.data / 'notes.sqlite3', self.data, self.data)
        self.lib.initialize([])
        self.body = dict(title='Tema', folder='', content='Texto original', shared=False,
                         documentId=None, page=None, anchors=[])

    def test_legacy_note_keeps_its_title_body_and_revision(self):
        note = self.lib.save_note(self.body)
        self.assertNotIn('contentFormat', note)
        self.assertEqual(self.lib.save_note(note), note)
        self.assertEqual(note_markdown(note, []), '# Tema\n\nTexto original\n')

    def test_full_document_keeps_title_once_and_preserves_old_version(self):
        original = self.lib.save_note(self.body)
        content = '# Tema nuevo\n\nTexto original\n\n# Otro encabezado'
        updated = self.lib.save_note({**original, 'title': 'Tema nuevo',
                                      'content': content, 'contentFormat': 'markdown'})
        self.assertEqual(updated['id'], original['id'])
        self.assertEqual(updated['content'], content)
        self.assertEqual(self.lib.save_note(updated), updated)
        self.assertEqual(self.lib.snapshot()['noteVersions'], [original])
        self.assertEqual(note_markdown(updated, []), content + '\n')
        self.assertEqual((self.data / 'notes' / (updated['id'] + '.md')).read_text(), content + '\n')
        backup = self.lib.snapshot()
        self.assertEqual(self.lib.validate_backup(backup), backup)

    def test_unknown_content_format_is_rejected(self):
        with self.assertRaises(ValueError):
            self.lib.save_note({**self.body, 'contentFormat': 'unknown'})

    def test_delete_keeps_evidence_and_rejects_stale_save_or_delete(self):
        original = self.lib.save_note({**self.body, 'shared': True})
        updated = self.lib.save_note({**original, 'content': 'Texto actualizado'})
        other = self.lib.save_note({**self.body, 'title': 'Otro apunte'})
        record = dict(id='tutor-test', noteId=original['id'], status='answered',
                      helpProvided=True, message='Consulta', reply='Ayuda',
                      context=dict(scope='general', noteRevision=original['revision']))
        with self.lib.connect() as conn:
            conn.execute('INSERT INTO note_tutor VALUES(?,?)', (record['id'], json.dumps(record)))
        with self.assertRaisesRegex(ValueError, 'otra ventana'):
            self.lib.delete_note(original)
        result = self.lib.delete_note(updated)
        self.assertEqual(result, self.lib.delete_note(updated))
        state = self.lib.snapshot()
        self.assertEqual(state['notes'], [other])
        self.assertEqual(state['deletedNotes'][0]['id'], original['id'])
        self.assertEqual(state['deletedNotes'][0]['content'], updated['content'])
        self.assertEqual(state['noteVersions'], [original, updated])
        self.assertEqual(state['noteTutor'], [record])
        self.assertFalse((self.data / 'notes' / (original['id'] + '.md')).exists())
        self.assertEqual(self.lib.author_context()['notes'], [])
        with self.assertRaisesRegex(ValueError, 'eliminado'):
            self.lib.save_note(updated)
        self.assertEqual(self.lib.validate_backup(state), state)
        restored = Library(self.data / 'restored.sqlite3', self.data / 'restored', self.data)
        restored.initialize([])
        with restored.connect() as conn:
            restored.restore(conn, state)
        self.assertEqual(restored.snapshot(), state)

    def test_pdf_highlight_geometry_and_selector_survive_and_are_validated(self):
        doc=dict(id='pdf-test',title='PDF temporal',sha256='0'*64,pages=1,storage='upload',filename='test.pdf')
        with self.lib.connect() as conn:
            conn.execute('INSERT INTO documents VALUES(?,?)',(doc['id'],json.dumps(doc)))
        anchor=dict(id='highlight',scope='page',documentId=doc['id'],sha256=doc['sha256'],page=1,quote='Texto',comment='',selector=dict(start=0,end=5),rects=[dict(x=.1,y=.2,width=.3,height=.04)])
        note=self.lib.save_note({**self.body,'documentId':doc['id'],'page':1,'anchors':[anchor]})
        self.assertEqual(note['anchors'],[anchor])
        for changed in ({'selector':dict(start=-1,end=5)},{'selector':dict(start=5,end=1)},{'rects':[]},{'rects':[dict(x=.9,y=0,width=.5,height=.1)]},{'rects':[dict(x=float('nan'),y=0,width=.5,height=.1)]},{'rects':[dict(x='0;display:none',y=0,width=.5,height=.1)]}):
            with self.subTest(changed=changed),self.assertRaises(ValueError):
                self.lib.save_note({**note,'anchors':[{**anchor,**changed}]})


if __name__ == '__main__':
    unittest.main()
