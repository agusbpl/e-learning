"""Folder discovery and tutorial isolation using temporary workspaces only."""
import json
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
        self.env = patch.dict('os.environ', {'GLOSA_MARGEN_DIR': ''})
        self.env.start(); self.addCleanup(self.env.stop)

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


if __name__ == '__main__':unittest.main()
