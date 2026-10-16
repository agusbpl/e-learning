"""Metadata de estudio dentro del apunte (library.validate_note/save_note).

Las propiedades de estudio (materia, unidad, fecha de parcial, necesito
practicar) y el registro de errores viajan como un campo `study` propio de la
nota, validado por library.py. No se crea ningún curso ni evento de feedback.
Base temporal; no toca datos reales.
"""
import tempfile
import unittest
from pathlib import Path

import note_files
from library import Library, note_markdown


class NoteStudyMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='glosa-study-metadata-')
        self.addCleanup(self.tmp.cleanup)
        self.data = Path(self.tmp.name)
        self.lib = Library(self.data / 'notes.sqlite3', self.data, self.data)
        self.lib.initialize([])
        self.body = dict(title='Derivadas', folder='', content='# Derivadas\n', contentFormat='markdown',
                         shared=False, documentId=None, page=None, anchors=[])
        self.study = dict(materia='Análisis matemático', unidad='Unidad 3', parcialDate='2026-11-15',
                          needsPractice=True, errors=[
                              dict(id='err-1', concept='Regla de la cadena', errorType='procedimiento',
                                   description='Olvidé la derivada interna.', correction='Multiplicar por g\u2032(x).',
                                   createdAt='2026-10-16T00:00:00+00:00')])

    def test_legacy_note_without_study_is_unchanged(self):
        note = self.lib.save_note(self.body)
        self.assertNotIn('study', note)
        self.assertEqual(self.lib.save_note(note), note)

    def test_study_is_persisted_with_revision_and_snapshot(self):
        note = self.lib.save_note({**self.body, 'study': self.study})
        self.assertEqual(note['study'], self.study)
        self.assertEqual(note['revision'], 1)
        stored = self.lib.snapshot()['notes'][0]
        self.assertEqual(stored['study'], self.study)
        again = self.lib.save_note({**note, 'study': {**self.study, 'needsPractice': False}})
        self.assertEqual(again['revision'], 2)
        self.assertFalse(again['study']['needsPractice'])
        self.assertEqual(self.lib.snapshot()['noteVersions'][0]['study'], self.study,
                         'la versión anterior conserva la metadata')

    def test_study_survives_backup_validation_and_restore(self):
        note = self.lib.save_note({**self.body, 'study': self.study})
        self.lib.save_note({**note, 'content': '# Derivadas\n\nCon un ejemplo.'})
        backup = self.lib.snapshot()
        self.assertEqual(self.lib.validate_backup(backup), backup)
        restored = Library(self.data / 'restored.sqlite3', self.data / 'restored', self.data)
        restored.initialize([])
        with restored.connect() as conn:
            restored.restore(conn, backup)
        self.assertEqual(restored.snapshot()['notes'][0]['study'], self.study)
        self.assertEqual(restored.snapshot()['noteVersions'][0]['study'], self.study)

    def test_unknown_study_field_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'desconocido'):
            self.lib.save_note({**self.body, 'study': {**self.study, 'dominio': True}})

    def test_invalid_parcial_date_and_practice_flag_are_rejected(self):
        for broken in ({'parcialDate': '15/11/2026'}, {'parcialDate': '2026-13-40'},
                       {'needsPractice': 'sí'}, {'materia': 3}, {'unidad': 'x' * 121}):
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                self.lib.save_note({**self.body, 'study': {**self.study, **broken}})

    def test_error_log_is_validated(self):
        base = {**self.study, 'errors': [dict(id='e', concept='Límites', errorType='concepto',
                                              description='', correction='', createdAt='')]}
        for broken in (
            {'errors': 'no'},
            {'errors': [{**base['errors'][0], 'errorType': 'magia'}]},
            {'errors': [{**base['errors'][0], 'concept': '   '}]},
            {'errors': [{**base['errors'][0], 'extra': 'x'}]},
            {'errors': [{**base['errors'][0], 'description': 'x' * 20001}]},
        ):
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                self.lib.save_note({**self.body, 'study': {**base, **broken}})
        self.assertEqual(self.lib.save_note({**self.body, 'study': base})['study']['errors'], base['errors'])

    def test_study_can_be_empty_and_needs_no_course(self):
        empty = dict(materia='', unidad='', parcialDate=None, needsPractice=False, errors=[])
        note = self.lib.save_note({**self.body, 'study': empty})
        self.assertEqual(note['study'], empty)

    def test_markdown_export_shows_properties_and_errors_without_touching_content(self):
        plain = self.lib.save_note(self.body)
        self.assertNotIn('Ficha de estudio', note_markdown(plain, []))
        empty = self.lib.save_note({**self.body, 'study': dict(materia='', unidad='', parcialDate=None, needsPractice=False, errors=[])})
        self.assertNotIn('Ficha de estudio', note_markdown(empty, []))
        note = self.lib.save_note({**self.body, 'study': self.study})
        text = note_markdown(note, [])
        self.assertTrue(text.startswith('# Derivadas\n'), 'el contenido original queda primero')
        self.assertIn('## Ficha de estudio', text)
        self.assertIn('- Materia: Análisis matemático', text)
        self.assertIn('- Unidad: Unidad 3', text)
        self.assertIn('- Fecha del parcial: 2026-11-15', text)
        self.assertIn('- Necesito practicar: sí', text)
        self.assertIn('### Errores de parcial', text)
        self.assertIn('**Regla de la cadena** · procedimiento', text)
        self.assertIn('Olvidé la derivada interna.', text)
        self.assertIn('Corrección: Multiplicar por g', text)
        # El original guarda el study como estructura auxiliar; el cuerpo queda
        # exactamente igual al texto de la persona.
        original = self.lib.note_file(note['id'])
        self.assertIsNotNone(original)
        info = note_files.read_note_file(original)
        self.assertEqual(info['content'], '# Derivadas\n')
        self.assertEqual(info['extras']['study'], self.study)
        self.assertIn('Regla de la cadena', original.read_text())


if __name__ == '__main__':
    unittest.main()
