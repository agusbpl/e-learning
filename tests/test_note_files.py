"""Formato del archivo Markdown original de los apuntes.

Estas pruebas defienden el contrato de roundtrip: el texto de la persona
(apunte general y de cada página) vive visible en el cuerpo, se conserva exacto
y se puede editar desde un editor externo sin que Glosa lo deforme.
"""
import tempfile
import unittest
from pathlib import Path

import note_files


def sample_note(**overrides):
    note = {
        'id': '3d05e432-b2c3-455c-8d57-6f9795af26e1',
        'revision': 2,
        'title': 'Clase sin filmina',
        'folder': 'Análisis/Unidad 3',
        'shared': True,
        'documentId': 'pdf-1',
        'page': 1,
        'writingScope': 'page',
        'contentFormat': 'body',
        'createdAt': '2026-10-16T17:42:37.441955+00:00',
        'updatedAt': '2026-10-16T17:42:37.441981+00:00',
        'content': '¿Cómo se relacionan? — Apunte original.\n\nSegunda línea con emoji 🚀',
        'pageNotes': {'pdf-1': {'1': 'PÁGINA UNO — duda', '2': 'PÁGINA DOS — explicación'}},
        'anchors': [{'id': 'general-comment', 'scope': 'general', 'documentId': None,
                     'page': None, 'sha256': None, 'quote': '', 'comment': 'Comentario independiente'}],
        'study': {'materia': 'Matemática', 'unidad': 'Derivadas', 'parcialDate': None,
                  'needsPractice': False, 'errors': []},
    }
    note.update(overrides)
    return note


class RoundTripTests(unittest.TestCase):
    def roundtrip(self, note, base=None):
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            path = Path(tmp)/'apunte.md'
            text, sync = note_files.render_note_file(note, base)
            path.write_text(text, encoding='utf-8')
            info = note_files.read_note_file(path)
            return text, sync, info

    def test_general_and_pages_roundtrip_exactly(self):
        note = sample_note()
        text, sync, info = self.roundtrip(note)
        self.assertEqual(info['content'], note['content'])
        self.assertEqual(info['pageNotes'], note['pageNotes'])
        self.assertEqual(info['glosa_id'], note['id'])
        self.assertEqual(info['revision'], note['revision'])
        self.assertEqual(info['extras']['anchors'], note['anchors'])
        self.assertEqual(info['extras']['study'], note['study'])
        self.assertEqual(sync, info['sync'])

    def test_render_is_idempotent_after_read(self):
        note = sample_note()
        text, sync, info = self.roundtrip(note)
        again, sync2 = note_files.render_note_file(
            note, {'front_lines': info['front_lines'], 'extras': info['extras']})
        self.assertEqual(again, text)
        self.assertEqual(sync2, sync)

    def test_page_text_is_visible_in_the_body(self):
        text, _sync, _info = self.roundtrip(sample_note())
        # El texto de cada página está en el cuerpo, no escondido en JSON.
        self.assertIn('<!-- glosa:page id="pdf-1" page="1" -->', text)
        self.assertIn('PÁGINA UNO — duda', text)
        self.assertIn('<!-- glosa:page id="pdf-1" page="2" -->', text)
        self.assertIn('PÁGINA DOS — explicación', text)
        # El comentario de datos sólo guarda estructura auxiliar.
        data_line = text.split('<!-- glosa:data', 1)[1]
        self.assertNotIn('PÁGINA UNO', data_line)
        self.assertIn('"anchors"', data_line)

    def test_editing_one_page_externally_does_not_move_the_others(self):
        note = sample_note()
        text, _sync, _info = self.roundtrip(note)
        edited = text.replace('PÁGINA DOS — explicación', 'PÁGINA DOS — texto editado a mano')
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            path = Path(tmp)/'apunte.md'
            path.write_text(edited, encoding='utf-8')
            info = note_files.read_note_file(path)
        self.assertEqual(info['pageNotes']['pdf-1']['2'], 'PÁGINA DOS — texto editado a mano')
        self.assertEqual(info['pageNotes']['pdf-1']['1'], 'PÁGINA UNO — duda')
        self.assertEqual(info['content'], note['content'])

    def test_foreign_frontmatter_keys_are_preserved(self):
        note = sample_note()
        head = ('---\n'
                'title: Nombre viejo\n'
                'tags: [clase, derivadas]\n'
                'cssclasses: wide\n'
                'glosa_id: '+note['id']+'\n'
                '---\n\n<!-- glosa:general -->\nx\n<!-- /glosa:general -->\n')
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            path = Path(tmp)/'apunte.md'
            path.write_text(head, encoding='utf-8')
            info = note_files.read_note_file(path)
        text, _sync = note_files.render_note_file(note, {'front_lines': info['front_lines'], 'extras': {}})
        self.assertIn('tags: [clase, derivadas]', text)
        self.assertIn('cssclasses: wide', text)
        self.assertNotIn('Nombre viejo', text)  # el título administrado se actualiza
        self.assertIn('title: '+note['title'], text)

    def test_bom_and_crlf_are_read_without_changing_visible_text(self):
        note = sample_note(content='Línea uno\nLínea dos')
        text, _sync = note_files.render_note_file(note)
        windows = text.replace('\n', '\r\n')
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            path = Path(tmp)/'apunte.md'
            path.write_bytes(b'\xef\xbb\xbf'+windows.encode('utf-8'))
            info = note_files.read_note_file(path)
        self.assertEqual(info['content'], 'Línea uno\nLínea dos')
        self.assertEqual(info['glosa_id'], note['id'])

    def test_non_utf8_is_a_recoverable_error(self):
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            path = Path(tmp)/'apunte.md'
            path.write_bytes(b'---\ntitle: x\n---\n\n\xff\xfe no es utf8')
            with self.assertRaises(note_files.NoteFormatError):
                note_files.read_note_file(path)

    def test_duplicate_page_is_an_error(self):
        note = sample_note()
        text, _sync = note_files.render_note_file(note)
        duplicated = text + '\n<!-- glosa:page id="pdf-1" page="1" -->\notra vez\n<!-- /glosa:page -->\n'
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            path = Path(tmp)/'apunte.md'
            path.write_text(duplicated, encoding='utf-8')
            with self.assertRaises(note_files.NoteFormatError):
                note_files.read_note_file(path)

    def test_unclosed_general_section_is_an_error(self):
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            path = Path(tmp)/'apunte.md'
            path.write_text('---\ntitle: x\n---\n\n<!-- glosa:general -->\nsin cierre', encoding='utf-8')
            with self.assertRaises(note_files.NoteFormatError):
                note_files.read_note_file(path)

    def test_human_file_without_markers_keeps_whole_body_as_general(self):
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            path = Path(tmp)/'apunte.md'
            path.write_text('# Título humano\n\nTexto suelto sin marcadores.\n', encoding='utf-8')
            info = note_files.read_note_file(path)
        # Sin frontmatter, el cuerpo completo es el apunte general, byte a byte.
        self.assertEqual(info['content'], '# Título humano\n\nTexto suelto sin marcadores.\n')
        self.assertEqual(info['pageNotes'], {})
        self.assertIsNone(info['glosa_id'])

    def test_titles_with_special_characters_roundtrip_in_frontmatter(self):
        note = sample_note(title='Colon: y "comillas"', folder='A/B')
        _text, _sync, info = self.roundtrip(note)
        self.assertEqual(info['meta']['title'], 'Colon: y "comillas"')
        self.assertEqual(info['meta']['folder'], 'A/B')

    def test_body_with_rules_and_user_comments_is_not_truncated(self):
        content = 'Primero\n\n---\n\nSegundo\n\n<!-- glosa:nota del usuario -->\n\nÚltimo'
        _text, _sync, info = self.roundtrip(sample_note(content=content))
        self.assertEqual(info['content'], content)


class PathSafetyTests(unittest.TestCase):
    def test_safe_segment_blocks_traversal(self):
        for raw in ('../../etc/passwd', '..', '.', 'a/b\\c', 'con\x00nul', '   '):
            segment = note_files.safe_segment(raw)
            self.assertNotIn('/', segment)
            self.assertNotIn('\\', segment)
            self.assertNotIn('\x00', segment)
            self.assertNotIn(segment, ('', '.', '..'))

    def test_relative_note_path_stays_inside_a_single_segment(self):
        rel = note_files.relative_note_path('../../etc', '../../evil')
        self.assertFalse(rel.startswith('/'))
        self.assertNotIn('..', rel.split('/'))
        self.assertTrue(rel.endswith('.md'))

    def test_folder_segments_drop_dotdot(self):
        self.assertEqual(note_files.folder_segments('../../etc'), ['etc'])

    def test_write_atomic_rejects_escape_and_symlink(self):
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            root = Path(tmp)/'root'
            (root).mkdir()
            outside = Path(tmp)/'outside.md'
            with self.assertRaises(note_files.NoteFileError):
                note_files.write_atomic(outside, 'x', root)
            link = root/'link'
            link.symlink_to(Path(tmp))
            with self.assertRaises(note_files.NoteFileError):
                note_files.write_atomic(link/'dentro.md', 'x', root)

    def test_write_atomic_conflict_preserves_existing_bytes(self):
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            root = Path(tmp)/'root'
            root.mkdir()
            target = root/'apunte.md'
            target.write_text('original', encoding='utf-8')
            with self.assertRaises(note_files.NoteConflictError):
                note_files.write_atomic(target, 'nuevo', root, expect=b'lo que yo lei')
            self.assertEqual(target.read_text(encoding='utf-8'), 'original')

    def test_write_atomic_no_file_guard_blocks_creation_race(self):
        with tempfile.TemporaryDirectory(prefix='glosa-note-files-') as tmp:
            root = Path(tmp)/'root'
            root.mkdir()
            target = root/'apunte.md'
            target.write_text('apareció', encoding='utf-8')
            with self.assertRaises(note_files.NoteConflictError):
                note_files.write_atomic(target, 'nuevo', root, expect=note_files.NO_FILE)
            self.assertEqual(target.read_text(encoding='utf-8'), 'apareció')
            target.unlink()
            note_files.write_atomic(target, 'nuevo', root, expect=note_files.NO_FILE)
            self.assertEqual(target.read_text(encoding='utf-8'), 'nuevo')
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
