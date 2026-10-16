"""Folder discovery and tutorial isolation using temporary workspaces only."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import rooms
import server
from scripts.room_backup import workspace


class MargenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='glosa-margen-')
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name)/'data'
        self.data.mkdir()
        # Never touch the real HOME: the default Margen must live in the fixture.
        self.home = Path(self.temp.name)/'home'
        self.home.mkdir()
        self.env = patch.dict('os.environ', {'HOME': str(self.home)})
        self.env.start(); self.addCleanup(self.env.stop)
        self.old_margen = os.environ.pop('GLOSA_MARGEN_DIR', None)
        self.addCleanup(self._restore_margen)

    def _restore_margen(self):
        if self.old_margen is not None:
            os.environ['GLOSA_MARGEN_DIR'] = self.old_margen

    def test_tutorial_is_separate_and_has_no_fabricated_history(self):
        with workspace(ROOT, self.data):
            server.init_db()
            original = server.snapshot()
        scope = rooms.room(self.data, ROOT, rooms.TUTORIAL_ID)
        with workspace(scope['root'], scope['data']):
            tutorial = server.snapshot()
            self.assertEqual([c['id'] for c in tutorial['courses']], ['glosa-primer-trazo'])
            self.assertEqual(tutorial['events'], [])
            self.assertEqual(tutorial['calendarEvents'], [])
            self.assertEqual(tutorial['library']['notes'], [])
            server.library().save_note({'title':'Práctica temporal','content':'Solo tutorial','folder':'', 'shared':False,'documentId':None,'page':None,'anchors':[]})
        with workspace(ROOT, self.data):
            state = server.snapshot()
            for key in ('courses', 'events', 'library', 'calendarEvents', 'settings'):
                self.assertEqual(state[key], original[key])

    def test_live_pliego_is_discovered_without_registry_and_writes_in_place(self):
        item = rooms.create(self.data, ROOT, 'Materia')
        self.assertFalse((self.data/'rooms.json').exists())
        scope = rooms.room(self.data, ROOT, item['id'])
        with workspace(scope['root'], scope['data']):
            self.assertEqual(server.snapshot()['courses'], [])
            note = server.library().save_note({'title':'Apunte','content':'Persistente','folder':'', 'shared':False,'documentId':None,'page':None,'anchors':[]})
        self.assertEqual(rooms.inventory(self.data, ROOT)['pliegos'][0]['id'], item['id'])
        with workspace(scope['root'], scope['data']):
            self.assertEqual(server.snapshot()['library']['notes'][0], note)

    def test_changing_margen_and_moving_folder_preserves_identity(self):
        item = rooms.create(self.data, ROOT, 'Mover')
        scope = rooms.room(self.data, ROOT, item['id'])
        new = Path(self.temp.name)/'another';new.mkdir()
        folder = scope['data'].parent
        folder.rename(new/folder.name)
        rooms.set_margen(self.data, str(new))
        self.assertEqual(rooms.room(self.data, ROOT, item['id'])['data'], new/folder.name/'learning')

    def test_duplicate_ids_are_reported_and_never_opened(self):
        item = rooms.create(self.data, ROOT, 'Original')
        folder = rooms.room(self.data, ROOT, item['id'])['data'].parent
        shutil.copytree(folder, folder.parent/'copy')
        listing = rooms.inventory(self.data, ROOT)
        self.assertEqual(listing['pliegos'], [])
        self.assertTrue(any('duplicado' in warning for warning in listing['warnings']))
        with self.assertRaises(ValueError):rooms.room(self.data, ROOT, item['id'])

    def test_symlinked_folder_and_database_are_not_discovered(self):
        item = rooms.create(self.data, ROOT, 'Original')
        scope = rooms.room(self.data, ROOT, item['id'])
        folder = scope['data'].parent
        (folder.parent/'alias').symlink_to(folder, target_is_directory=True)
        self.assertEqual(len(rooms.inventory(self.data, ROOT)['pliegos']), 1)
        db = scope['data']/'learning.sqlite3'
        real = db.with_suffix('.original');db.rename(real);db.symlink_to(real)
        self.assertEqual(rooms.inventory(self.data, ROOT)['pliegos'], [])

    def test_legacy_registered_room_is_still_available(self):
        item = rooms.create(self.data, ROOT, 'Anterior')
        folder = rooms.room(self.data, ROOT, item['id'])['data'].parent
        legacy = self.data/'rooms'/item['id'];legacy.parent.mkdir()
        folder.rename(legacy)
        (legacy/'pliego.json').unlink()
        (self.data/'rooms.json').write_text(json.dumps([item]))
        self.assertEqual(rooms.room(self.data, ROOT, item['id'])['data'], legacy/'learning')

    def test_invalid_margen_and_environment_override(self):
        for folder in ('relative', str(Path(self.temp.name)/'missing'), None):
            with self.subTest(folder=folder),self.assertRaises(ValueError):rooms.set_margen(self.data, folder)
        with patch.dict('os.environ', {'GLOSA_MARGEN_DIR': str(self.data)}):
            self.assertEqual(rooms.margen(self.data)['source'], 'environment')
            with self.assertRaises(ValueError):rooms.set_margen(self.data, str(self.data))

    def test_default_margen_is_visible_and_creates_home_folder(self):
        location = rooms.margen(self.data)
        self.assertEqual(location['source'], 'default')
        self.assertEqual(location['path'], str((self.home/'Margen').resolve()))
        self.assertTrue((self.home/'Margen').is_dir())

    def test_create_uses_human_folder_and_unique_names(self):
        first = rooms.create(self.data, ROOT, 'Análisis Numérico')
        self.assertEqual(Path(first['path']).name, 'Análisis Numérico')
        self.assertTrue(first['id'].startswith('pliego-'))
        second = rooms.create(self.data, ROOT, 'Análisis Numérico')
        self.assertEqual(Path(second['path']).name, 'Análisis Numérico (2)')
        self.assertNotEqual(first['id'], second['id'])
        # A title is data: it can never escape the Margen through the folder name.
        self.assertNotIn('/', rooms.safe_folder_name('../../etc/passwd'))
        self.assertNotIn('..', rooms.safe_folder_name('..'))

    def test_local_alias_marker_redirects_and_stales_on_change(self):
        source_db = self.data/'learning.sqlite3'
        source_db.write_bytes(b'sqlite-original')
        vault = self.home/'Margen'/'Biblioteca local'
        (vault/'assets').mkdir(parents=True)
        (vault/'learning').mkdir()
        (vault/'learning/learning.sqlite3').write_bytes(b'sqlite-copy')
        (vault/'pliego.json').write_text(json.dumps(
            {'format': 'glosa-pliego', 'version': 1, 'id': 'local', 'title': 'Biblioteca local'}))
        stat = source_db.stat()
        (self.data/rooms.LOCAL_ALIAS_FILE).write_text(json.dumps(
            {'format': 'glosa-local-alias', 'version': 1, 'id': 'local', 'title': 'Biblioteca local',
             'path': str(vault), 'original': {'bytes': stat.st_size, 'mtimeNs': stat.st_mtime_ns}}))
        scope = rooms.local_scope(self.data)
        self.assertIsNotNone(scope)
        self.assertEqual(scope['id'], 'local')
        self.assertEqual(scope['data'], vault/'learning')
        self.assertEqual(scope['root'], vault/'assets')
        self.assertEqual(rooms.room(self.data, ROOT, 'local')['data'], vault/'learning')
        # The original active database changed after the copy: never activate a stale alias.
        source_db.write_bytes(b'sqlite-original-changed-later')
        warnings = []
        self.assertIsNone(rooms.local_scope(self.data, warnings))
        self.assertTrue(any('cambió' in warning for warning in warnings))

    def test_invalid_local_alias_marker_never_falls_back_silently(self):
        source_db = self.data/'learning.sqlite3'
        source_db.write_bytes(b'sqlite-original')
        # Without a marker, 'local' legitimately uses the application data dir.
        self.assertEqual(rooms.room(self.data, ROOT, 'local')['data'], self.data)
        # Marker present but pointing to a vanished/invalid vault.
        (self.data/rooms.LOCAL_ALIAS_FILE).write_text(json.dumps(
            {'format': 'glosa-local-alias', 'version': 1, 'id': 'local', 'title': 'Biblioteca local',
             'path': str(self.home/'Margen'/'desaparecida'), 'original': {'bytes': 1, 'mtimeNs': 1}}))
        warnings = []
        self.assertIsNone(rooms.local_scope(self.data, warnings))
        self.assertTrue(warnings)
        with self.assertRaises(ValueError):
            rooms.room(self.data, ROOT, 'local')
        # El error recuperable conserva ambas copias: la base original no se tocó.
        self.assertEqual(source_db.read_bytes(), b'sqlite-original')
        # El listado sigue usable e incluye la entrada local.
        self.assertIn('local', [item['id'] for item in rooms.list_rooms(self.data, ROOT)])

    def test_duplicate_ids_expose_both_paths(self):
        item = rooms.create(self.data, ROOT, 'Original')
        folder = rooms.room(self.data, ROOT, item['id'])['data'].parent
        shutil.copytree(folder, folder.parent/'copy')
        listing = rooms.inventory(self.data, ROOT, details=False)
        self.assertEqual(len(listing['duplicates'].get(item['id'], [])), 2)

    def test_inventory_scans_legacy_margen_folder(self):
        legacy = self.data/'margen'/'Vieja'
        (legacy/'assets').mkdir(parents=True)
        (legacy/'learning').mkdir()
        (legacy/'learning/learning.sqlite3').write_bytes(b'')
        (legacy/'pliego.json').write_text(json.dumps(
            {'format': 'glosa-pliego', 'version': 1, 'id': 'pliego-vieja', 'title': 'Vieja'}))
        listing = rooms.inventory(self.data, ROOT, details=False)
        self.assertEqual([item['id'] for item in listing['pliegos']], ['pliego-vieja'])


if __name__ == '__main__':unittest.main()
