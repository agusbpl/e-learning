"""Migración segura a un Margen visible: plan/dry-run/apply/verify y recuperación.

Todo ocurre en espacios temporales: HOME, datos y respaldo viven bajo el
directorio temporal del test. Nunca se toca `~/Margen` real ni el repositorio,
y no se llama a ningún proveedor.
"""
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
sys.path.insert(0, str(ROOT/'scripts'))
import rooms
import server
import migrate_vaults as migration
from scripts.room_backup import workspace, verify_bundle


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='glosa-migracion-')
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.base = base
        self.home = base/'home'
        self.home.mkdir()
        self.env = patch.dict('os.environ', {'HOME': str(self.home)})
        self.env.start(); self.addCleanup(self.env.stop)
        self.old_margen = os.environ.pop('GLOSA_MARGEN_DIR', None)
        self.addCleanup(self._restore_margen)
        self.root = base/'root'
        (self.root/'sources').mkdir(parents=True)
        (self.root/'.md_cache').mkdir()
        (self.root/'courses').mkdir()
        shutil.copyfile(server.ROOT/'courses/tutorial.json', self.root/'courses/default.json')
        self.data = base/'data'
        self.data.mkdir()
        with workspace(self.root, self.data):
            server.init_db()
            state = server.snapshot()
            self.course_id = state['courses'][0]['id']
            self.lesson_id = state['courses'][0]['lessons'][0]['id']
            self.course_version = state['courses'][0]['version']
            server.event('visit', self.course_id, self.lesson_id, {'courseVersion': self.course_version}, 'trace-local')
            server.library().save_note({'title': 'Apunte local', 'folder': '', 'content': 'Contenido base',
                                        'shared': False, 'documentId': None, 'page': None, 'anchors': []})
        (self.data/'Apuntes').mkdir(exist_ok=True)
        (self.data/'Apuntes'/'Apunte local.md').write_text('# Apunte local\n\nEdición externa local\n', encoding='utf-8')
        (self.data/'notes').mkdir()
        (self.data/'notes'/'viejo.md').write_text('espejo viejo\n', encoding='utf-8')
        (self.data/'documents').mkdir()
        (self.data/'documents'/'local.pdf').write_bytes(b'%PDF-1.4\n%%EOF\n')

    def _restore_margen(self):
        if self.old_margen is not None:
            os.environ['GLOSA_MARGEN_DIR'] = self.old_margen

    def _make_pliego(self, title):
        created = rooms.create(self.data, self.root, title)
        scope = rooms.room(self.data, self.root, created['id'])
        with workspace(scope['root'], scope['data']):
            server.library().save_note({'title': 'Apunte '+title, 'folder': '', 'content': 'Contenido '+title,
                                        'shared': False, 'documentId': None, 'page': None, 'anchors': []})
        return created

    def _make_pliego_marked(self, title, marker):
        created = self._make_pliego(title)
        scope = rooms.room(self.data, self.root, created['id'])
        with workspace(scope['root'], scope['data']):
            server.library().save_note({'title': marker, 'folder': '', 'content': 'Contenido '+marker,
                                        'shared': False, 'documentId': None, 'page': None, 'anchors': []})
        return created

    def _notes_text(self, folder):
        text = []
        if Path(folder).is_dir():
            for entry in sorted(Path(folder).rglob('*.md')):
                text.append(entry.read_text(encoding='utf-8'))
        return '\n'.join(text)

    def test_plan_is_read_only_and_creates_nothing(self):
        before = migration._tree_digests(self.base)
        plan = migration.plan_migration(self.data, self.root)
        after = migration._tree_digests(self.base)
        self.assertEqual(before, after, 'plan no debe escribir nada')
        self.assertFalse((self.home/'Margen').exists(), 'el Margen por defecto no se crea al planificar')
        self.assertEqual(plan['target'], str((self.home/'Margen').resolve()))
        self.assertEqual(plan['local']['action'], 'copy')
        self.assertEqual(plan['collisions'], [])

    def test_uuid_folder_is_renamed_to_human_name_and_idempotent(self):
        created = self._make_pliego('Álgebra')
        folder = Path(created['path'])
        ugly = folder.parent/created['id']
        folder.rename(ugly)
        plan = migration.plan_migration(self.data, self.root)
        item = next(entry for entry in plan['items'] if entry['id'] == created['id'])
        self.assertEqual(item['action'], 'move')
        self.assertEqual(Path(item['to']).name, 'Álgebra')
        migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        moved = self.home/'Margen'/'Álgebra'
        self.assertTrue((moved/'pliego.json').is_file())
        self.assertFalse(ugly.exists())
        self.assertEqual(json.loads((moved/'pliego.json').read_text())['id'], created['id'])
        scope = rooms.room(self.data, self.root, created['id'])
        with workspace(scope['root'], scope['data']):
            state = server.snapshot()
            self.assertEqual(state['library']['notes'][0]['content'], 'Contenido Álgebra')
        again = migration.plan_migration(self.data, self.root)
        self.assertTrue(all(entry['action'] == 'none' for entry in again['items']))

    def test_legacy_registered_pliego_without_metadata_migrates_notes(self):
        folder = self.data/'rooms'/'pliego-legado'
        (folder/'learning').mkdir(parents=True)
        (folder/'assets').mkdir()
        with workspace(folder/'assets', folder/'learning'):
            server.init_db()
            server.event('visit', 'fixture-course', 'fixture-lesson', {'courseVersion': '1.0.0'}, 'trace-legado')
            server.library().save_note({'title': 'Nota legado', 'folder': '', 'content': 'Contenido legado',
                                        'shared': False, 'documentId': None, 'page': None, 'anchors': []})
        (folder/'learning'/'Apuntes').mkdir(exist_ok=True)
        (folder/'learning'/'Apuntes'/'legado.md').write_text('# legado\n\nEdición externa legado\n', encoding='utf-8')
        (self.data/'rooms.json').write_text(json.dumps([{'id': 'pliego-legado', 'title': 'Legado', 'path': str(folder)}]))
        plan = migration.plan_migration(self.data, self.root)
        item = next(entry for entry in plan['items'] if entry['id'] == 'pliego-legado')
        self.assertFalse(item['metadata'])
        migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        landed = self.home/'Margen'/'Legado'
        self.assertTrue((landed/'pliego.json').is_file())
        metadata = json.loads((landed/'pliego.json').read_text())
        self.assertEqual((metadata['id'], metadata['title']), ('pliego-legado', 'Legado'))
        self.assertFalse((landed/'learning'/'Apuntes').exists())
        self.assertIn('Edición externa legado', self._notes_text(landed/'Apuntes'))
        stored = json.loads((self.data/'rooms.json').read_text())
        self.assertEqual(stored[0]['path'], str(landed))
        scope = rooms.room(self.data, self.root, 'pliego-legado')
        with workspace(scope['root'], scope['data']):
            state = server.snapshot()
            self.assertEqual([e['id'] for e in state['events']], ['trace-legado'])

    def test_apply_moves_all_pliegos_and_local_with_verified_backup(self):
        created = self._make_pliego('Análisis Numérico')
        result = migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        moved = self.home/'Margen'/'Análisis Numérico'
        local = self.home/'Margen'/'Biblioteca local'
        self.assertTrue((moved/'pliego.json').is_file())
        self.assertTrue((local/'pliego.json').is_file())
        self.assertEqual(json.loads((local/'pliego.json').read_text())['id'], 'local')
        marker = json.loads((self.data/'local-migrated.json').read_text())
        self.assertEqual(marker['id'], 'local')
        self.assertIn('Edición externa local', self._notes_text(local/'Apuntes'))
        self.assertIn('espejo viejo', self._notes_text(local/'notes-legacy'))
        state, _ = verify_bundle(self.base/'respaldo'/'pliegos'/created['id'])
        self.assertEqual(len(state['library']['notes']), 1)
        verify_bundle(self.base/'respaldo'/'local')
        scope = rooms.room(self.data, self.root, 'local')
        self.assertEqual(scope['data'], local/'learning')
        self.assertEqual(result['problems'], [])

    def test_apply_is_idempotent(self):
        self._make_pliego('Idempotente')
        migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        before = sorted(p.name for p in (self.home/'Margen').iterdir())
        migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        after = sorted(p.name for p in (self.home/'Margen').iterdir())
        self.assertEqual(before, after)
        self.assertFalse(any('(' in name for name in after), 'no debe duplicar con sufijo en la segunda corrida')

    def test_foreign_folder_collision_aborts_without_merging(self):
        created = self._make_pliego('Colisión')
        legacy = self.data/'margen'
        legacy.mkdir()
        Path(created['path']).rename(legacy/'Colisión')
        foreign = self.home/'Margen'/'Colisión'
        foreign.mkdir()
        (foreign/'nota.txt').write_text('contenido ajeno')
        plan = migration.plan_migration(self.data, self.root)
        self.assertTrue(plan['collisions'])
        with self.assertRaises(ValueError):
            migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        self.assertEqual((foreign/'nota.txt').read_text(), 'contenido ajeno')
        self.assertTrue((legacy/'Colisión'/'pliego.json').is_file())

    def test_backup_must_live_outside_repository(self):
        with self.assertRaises(ValueError):
            migration.apply_migration(self.data, self.root, None, ROOT/'tmp-respaldo-migracion')
        with self.assertRaises(ValueError):
            migration.apply_migration(self.data, self.root, None, None)

    def test_recovery_finds_moved_pliego_by_metadata(self):
        created = self._make_pliego('Recuperable')
        legacy = self.data/'margen'
        legacy.mkdir()
        Path(created['path']).rename(legacy/'Recuperable')
        (self.data/'rooms.json').write_text(json.dumps([
            {'id': created['id'], 'title': 'Recuperable', 'path': str(legacy/'Recuperable')}]))
        # Crash simulation: the folder already moved, the registry/journal did not update.
        destination = self.home/'Margen'/'Recuperable'
        (legacy/'Recuperable').rename(destination)
        (self.home/'Margen'/migration.LOCK_NAME).write_text('{}')
        (self.home/'Margen'/(migration.STAGE_PREFIX+'resto')).mkdir()
        plan = migration.plan_migration(self.data, self.root)
        item = next(entry for entry in plan['items'] if entry['id'] == created['id'])
        self.assertEqual(item['action'], 'none')
        with self.assertRaises(ValueError):
            migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        migration.apply_migration(self.data, self.root, None, self.base/'respaldo', recovery=True)
        stored = json.loads((self.data/'rooms.json').read_text())
        self.assertEqual(stored[0]['path'], str(destination))
        self.assertFalse((self.home/'Margen'/(migration.STAGE_PREFIX+'resto')).exists())
        self.assertFalse((self.home/'Margen'/migration.LOCK_NAME).exists())
        self.assertEqual(len(list((self.home/'Margen').glob('Recuperable*'))), 1)

    def test_plan_does_not_prune_mover_leftovers(self):
        stale = self.data/'mover-restos.json'
        stale.write_text(json.dumps([{'path': str(self.base/'noexiste'), 'at': 'x'}]))
        before = stale.read_bytes()
        migration.plan_migration(self.data, self.root)
        self.assertEqual(stale.read_bytes(), before, 'plan/dry-run debe ser de solo lectura')

    def test_apply_imports_external_edit_without_aborting(self):
        created = self._make_pliego('Editable')
        vault = Path(created['path'])
        note_file = vault/'Apuntes'/'Apunte Editable.md'
        self.assertTrue(note_file.is_file())
        note_file.write_text(note_file.read_text(encoding='utf-8').replace('Contenido Editable', 'EDITADO EXTERNO'),
                             encoding='utf-8')
        legacy = self.data/'margen'
        legacy.mkdir()
        vault.rename(legacy/'Editable')  # fuerza la acción 'move'
        result = migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        self.assertEqual(result['problems'], [])
        landed = self.home/'Margen'/'Editable'
        self.assertEqual(json.loads((landed/'pliego.json').read_text())['id'], created['id'])
        self.assertIn('EDITADO EXTERNO', self._notes_text(landed/'Apuntes'))
        with workspace(landed/'assets', landed/'learning'):
            self.assertEqual([n['content'] for n in server.snapshot()['library']['notes']], ['EDITADO EXTERNO'])

    def test_local_copy_is_verified_bytewise_and_keeps_original(self):
        original_pdf = (self.data/'documents'/'local.pdf').read_bytes()
        real_copy2 = shutil.copy2

        def corrupting_copy2(source, destination, *args, **kwargs):
            result = real_copy2(source, destination, *args, **kwargs)
            if Path(destination).name == 'local.pdf':
                Path(destination).write_bytes(b'%PDF-1.4\nCORRUPTO\n')
            return result

        with patch('migrate_vaults.shutil.copy2', side_effect=corrupting_copy2):
            with self.assertRaises(ValueError):
                migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        self.assertEqual((self.data/'documents'/'local.pdf').read_bytes(), original_pdf)
        self.assertFalse((self.home/'Margen'/'Biblioteca local').exists(),
                         'una copia no verificada no debe quedar activa')

    def test_duplicate_id_blocks_apply_without_deleting(self):
        created = self._make_pliego('Duplicado')
        legacy = self.data/'margen'
        legacy.mkdir()
        Path(created['path']).rename(legacy/'Duplicado')
        (self.data/'rooms.json').write_text(json.dumps([
            {'id': created['id'], 'title': 'Duplicado', 'path': str(legacy/'Duplicado')}]))
        target = self.home/'Margen'
        target.mkdir(exist_ok=True)
        shutil.copytree(legacy/'Duplicado', target/'Duplicado')  # copia ya completa (crash cross-device)
        plan = migration.plan_migration(self.data, self.root)
        self.assertTrue(any(collision['id'] == created['id'] for collision in plan['collisions']))
        with self.assertRaises(ValueError):
            migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        self.assertTrue((legacy/'Duplicado'/'pliego.json').is_file())
        self.assertTrue((target/'Duplicado'/'pliego.json').is_file())

    def test_duplicate_titles_keep_stable_unique_names_and_second_plan_is_none(self):
        # Dos pliegos con el MISMO título pero contenido distinto (IDs y notas
        # propias) deben conservarse ambos: uno recibe el nombre base y el otro
        # un sufijo estable. Un segundo plan no debe proponer renombrar el
        # sufijo a otro número (renombrado infinito).
        first = self._make_pliego_marked('Tecnologías para la Gestión', 'marca-uno')
        second = self._make_pliego_marked('Tecnologías para la Gestión', 'marca-dos')
        self.assertNotEqual(first['id'], second['id'])
        legacy = self.data/'margen'
        legacy.mkdir(exist_ok=True)
        Path(first['path']).rename(legacy/Path(first['path']).name)
        Path(second['path']).rename(legacy/Path(second['path']).name)

        plan = migration.plan_migration(self.data, self.root)
        planned = {entry['id']: entry for entry in plan['items']}
        self.assertEqual(planned[first['id']]['action'], 'move')
        self.assertEqual(planned[second['id']]['action'], 'move')
        self.assertEqual({Path(entry['to']).name for entry in plan['items']},
                         {'Tecnologías para la Gestión', 'Tecnologías para la Gestión (2)'})

        migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        target = self.home/'Margen'
        for name in ('Tecnologías para la Gestión', 'Tecnologías para la Gestión (2)'):
            self.assertTrue((target/name/'pliego.json').is_file(), name)
        # Cada pliego conserva su ID y su nota propios (contenido diferente).
        self.assertEqual(json.loads((target/'Tecnologías para la Gestión'/'pliego.json').read_text())['id'], first['id'])
        self.assertEqual(json.loads((target/'Tecnologías para la Gestión (2)'/'pliego.json').read_text())['id'], second['id'])
        self.assertIn('Contenido marca-uno', self._notes_text(target/'Tecnologías para la Gestión'/'Apuntes'))
        self.assertIn('Contenido marca-dos', self._notes_text(target/'Tecnologías para la Gestión (2)'/'Apuntes'))

        # Segundo plan: ambos pliegos ya tienen un nombre humano único estable.
        again = migration.plan_migration(self.data, self.root)
        for entry in again['items']:
            self.assertEqual(entry['action'], 'none', entry)
        self.assertEqual(again['collisions'], [])

        # Un tercer apply no mueve ni crea carpetas nuevas (sin "(3)").
        before = sorted(p.name for p in target.iterdir())
        migration.apply_migration(self.data, self.root, None, self.base/'respaldo')
        after = sorted(p.name for p in target.iterdir())
        self.assertEqual(before, after)
        self.assertFalse(any(name.endswith('(3)') for name in after), after)

    def test_opaque_id_folder_inside_target_is_still_renamed(self):
        # Un nombre opaco (el ID) NUNCA se acepta como nombre humano: dentro del
        # Margen destino la carpeta se sigue renombrando al título.
        created = self._make_pliego('Óptica')
        folder = Path(created['path'])
        ugly = folder.parent/created['id']
        folder.rename(ugly)
        plan = migration.plan_migration(self.data, self.root)
        item = next(entry for entry in plan['items'] if entry['id'] == created['id'])
        self.assertEqual(item['action'], 'move')
        self.assertEqual(Path(item['to']).name, 'Óptica')



if __name__ == '__main__':
    unittest.main()
