"""Complete authoring delivery, isolated from the student's Margen and history."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent/'helpers'))
import author_pliego
import server
import rooms
from fixture_workspace import fixture_pdf


class AuthorPliegoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='glosa-author-pliego-')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.data = self.path/'data'; self.data.mkdir()
        self.margen = self.path/'vaults'; self.margen.mkdir()
        self.sources = self.path/'sources'; self.sources.mkdir()
        self.env = patch.dict(os.environ, {'GLOSA_MARGEN_DIR': str(self.margen),
                                          'LEARNING_DATA_DIR': str(self.data)})
        self.env.start(); self.addCleanup(self.env.stop)
        self.globals = patch.multiple(server, DATA=self.data, DB=self.data/'learning.sqlite3')
        self.globals.start(); self.addCleanup(self.globals.stop)
        self.course = {'schemaVersion': 1, 'id': 'test-course', 'version': '1', 'title': 'Curso temporal',
                       'sources': [], 'lessons': [{'id': 'one', 'title': 'Tema', 'minutes': 30,
                       'priority': 1, 'prerequisites': [], 'blocks': [{'id': 'b', 'title': 'Texto', 'text': 'Concepto'}],
                       'exercises': [{'id': 'e', 'type': 'explain', 'question': 'Explicá la relación.',
                                      'rubric': ['Relaciona dos conceptos']}]}]}
        (self.sources/'teoria.md').write_text('Contenido autorizado\n'*15000)

    def validate(self, course):
        server.validate_course(course)
        for source in course.get('sources', []):
            doc = server.library().document(source['url'].removeprefix('/documents/'))
            self.assertTrue(server.library().document_path(doc).is_file())
        return {'valid': True, 'warnings': []}

    def create(self, **kwargs):
        return author_pliego.create(server, str(self.sources), 'Materia nueva', self.course,
                                    'Fuentes y revisión semántica declaradas.', self.validate, **kwargs)

    def test_ready_directory_sources_course_calendar_and_no_drafts(self):
        result = self.create(study_plan={'examDate': '2026-10-20', 'dailyOverrides': {'2026-10-18': 30}},
                             calendar_events=[{'title': 'Parcial', 'kind': 'exam', 'date': '2026-10-20', 'time': '19:00'}])
        target = Path(result['path'])
        self.assertEqual(target.parent, self.margen)
        self.assertEqual(result['status'], 'ready')
        self.assertTrue((target/'pliego.json').is_file())
        scope = rooms.room(self.data, server.ROOT, result['id'])
        token = server.ACTIVE_WORKSPACE.set(scope)
        try:
            state = server.snapshot()
            self.assertEqual(state['courses'], [self.course])
            self.assertEqual(state['events'], [])
            self.assertEqual(state['library']['courseDrafts'], [])
            notes = sorted(state['library']['notes'], key=lambda n:n['id'])
            self.assertEqual(''.join(n['content'] for n in notes), (self.sources/'teoria.md').read_text())
            self.assertEqual(state['calendarEvents'][0]['time'], '19:00')
            self.assertEqual(state['settings']['dailyOverrides'], {'2026-10-18': 30})
        finally:
            server.ACTIVE_WORKSPACE.reset(token)
        second = self.create()
        self.assertNotEqual(second['path'], result['path'])
        self.assertTrue(target.exists())
        self.assertFalse(any(self.margen.glob('*.zip')))

    def test_failure_never_publishes_empty_vault(self):
        self.course['lessons'] = []
        with self.assertRaises(ValueError): self.create()
        self.assertEqual(list(self.margen.iterdir()), [])

    def test_bad_calendar_or_plan_rolls_back(self):
        for kwargs in ({'study_plan': {'dailyOverrides': {'2026-10-18': -1}}},
                       {'calendar_events': [{'title': 'Parcial', 'kind': 'exam', 'date': 'not-a-date'}]}):
            with self.assertRaises(ValueError): self.create(**kwargs)
            self.assertEqual(list(self.margen.iterdir()), [])

    def test_inventory_rejects_external_links_and_selected_traversal(self):
        outside = self.path/'private.md'; outside.write_text('No autorizado')
        (self.sources/'link.md').symlink_to(outside)
        info = author_pliego.inventory(str(self.sources))
        self.assertEqual([f['path'] for f in info['files']], ['teoria.md'])
        with self.assertRaises(ValueError):
            author_pliego.inventory(str(self.sources), ['../private.md'])

    def test_pdf_ids_references_and_cache_travel_in_directory(self):
        raw = fixture_pdf(); (self.sources/'clase.pdf').write_bytes(raw)
        doc_id = 'doc-'+hashlib.sha256(raw).hexdigest()[:24]
        self.course['sources'] = [{'id': 'pdf', 'title': 'Clase', 'url': '/documents/'+doc_id}]
        self.course['lessons'][0]['blocks'][0]['references'] = [{'sourceId': 'pdf', 'page': 1}]
        result = self.create(source_files=['clase.pdf'])
        scope = rooms.room(self.data, server.ROOT, result['id'])
        token = server.ACTIVE_WORKSPACE.set(scope)
        try:
            self.assertEqual(len(server.library().snapshot()['documents']), 1)
            self.assertEqual(server.library().pages(doc_id)['pages'][0]['page'], 1)
            self.assertEqual(server.library().snapshot()['notes'], [])
        finally: server.ACTIVE_WORKSPACE.reset(token)

    def test_configured_margen_precedes_default(self):
        self.create()
        self.assertEqual(len(list(self.margen.iterdir())), 1)
        self.assertFalse((self.path/'Margen').exists())

    def test_folder_chooser_lists_only_directories_without_reading_files(self):
        (self.sources/'Unidad 1').mkdir()
        (self.sources/'.privado').mkdir()
        (self.sources/'enlace').symlink_to(self.path, target_is_directory=True)
        result = author_pliego.browse_folders(str(self.sources))
        self.assertEqual(result['path'], str(self.sources))
        self.assertEqual(result['directories'], [{'name': 'Unidad 1', 'path': str(self.sources/'Unidad 1')}])
        self.assertEqual(result['parent'], str(self.path))
        self.assertEqual(list(self.margen.iterdir()), [])
        with self.assertRaises(ValueError): author_pliego.browse_folders('ruta/relativa')
        with self.assertRaises(ValueError): author_pliego.browse_folders(str(self.sources/'teoria.md'))


if __name__ == '__main__': unittest.main()
