"""Temporary workspaces only: portable backups and room isolation."""
import base64
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
import rooms
from scripts.room_backup import export_room, restore_room, verify_bundle, workspace


class RoomTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='glosa-room-test-')
        self.path = Path(self.temp.name)
        self.root, self.data = self.path/'root', self.path/'data'
        self.root.mkdir(); self.data.mkdir()
        (self.root/'courses').mkdir()
        # The visible Margen defaults to HOME/Margen: keep it inside the fixture.
        self.home = self.path/'home'
        self.home.mkdir()
        self.env = patch.dict('os.environ', {'HOME': str(self.home)})
        self.env.start(); self.addCleanup(self.env.stop)
        self.old_margen = os.environ.pop('GLOSA_MARGEN_DIR', None)
        self.addCleanup(self._restore_margen)
        # Use the public tutorial fixture, never a student's course.
        shutil.copyfile(server.ROOT/'courses/tutorial.json', self.root/'courses/default.json')
        with workspace(self.root, self.data):
            server.init_db()
            self.course_id = server.snapshot()['courses'][0]['id']
            self.lesson_id = server.snapshot()['courses'][0]['lessons'][0]['id']
            self.course_version = server.snapshot()['courses'][0]['version']
            server.library().save_note({'title':'Apunte QA','folder':'','content':'Texto persistente',
                                       'shared':False,'documentId':None,'page':None,'anchors':[]})
            server.event('visit',self.course_id,self.lesson_id,{'courseVersion':self.course_version},'trace-1')
        self.bundle = self.path/'bundle'
        export_room(self.bundle, self.data, self.root)

    def _restore_margen(self):
        if self.old_margen is not None:
            os.environ['GLOSA_MARGEN_DIR'] = self.old_margen

    def tearDown(self):
        self.temp.cleanup()

    def test_round_trip_and_refuse_existing_history(self):
        output, root = self.path/'restored', self.path/'new-root'
        root.mkdir()
        restore_room(self.bundle, output, root)
        with workspace(root, output):
            self.assertEqual(server.snapshot()['events'][0]['id'], 'trace-1')
            self.assertEqual(server.snapshot()['library']['notes'][0]['content'], 'Texto persistente')
        with self.assertRaisesRegex(ValueError, 'vacía'):
            restore_room(self.bundle, output, root)

    def test_restore_reconstructs_raw_notes_without_duplicates(self):
        """Un apunte crudo (`Uno.md`) vuelve atado a su ID, sin duplicar `Concepto.md`."""
        notes_root = self.data/'Apuntes'
        notes_root.mkdir(parents=True, exist_ok=True)
        (notes_root/'Uno.md').write_text('# Concepto\n\nCuerpo uno externo.\n', encoding='utf-8')
        (notes_root/'Dos.md').write_text('# Distinto\n\nCuerpo dos externo.\n', encoding='utf-8')
        with workspace(self.root, self.data):
            before = server.snapshot()
        externals = [n for n in before['library']['notes'] if 'externo' in n['content']]
        self.assertEqual(len(externals), 2)
        ids = sorted(n['id'] for n in externals)
        bundle = self.path/'bundle-raw'
        export_room(bundle, self.data, self.root)
        manifest = json.loads((bundle/'manifest.json').read_text())
        # La identidad portable viaja en el respaldo.
        self.assertIn('apuntes/originales/.glosa-identidad.json', manifest['files'])
        self.assertTrue((bundle/'apuntes/originales/Uno.md').is_file())
        output, root = self.path/'restored-raw', self.path/'new-root-raw'
        root.mkdir()
        restore_room(bundle, output, root)
        with workspace(root, output):
            after = server.snapshot()
        externals_after = [n for n in after['library']['notes'] if 'externo' in n['content']]
        # Mismos IDs, mismos contenidos, ninguna nota perdida ni agregada.
        self.assertEqual(sorted(n['id'] for n in externals_after), ids)
        self.assertEqual(len(after['library']['notes']), len(before['library']['notes']))
        self.assertEqual(sorted(n['content'] for n in externals_after),
                         sorted(n['content'] for n in externals))
        files = sorted(p.relative_to(output/'Apuntes').as_posix()
                       for p in (output/'Apuntes').rglob('*.md'))
        self.assertIn('Uno.md', files)
        self.assertIn('Dos.md', files)
        # No reaparece el nombre derivado del título.
        self.assertNotIn('Concepto.md', files)
        self.assertNotIn('Distinto.md', files)

    def test_backup_carries_recovery_folders_without_adopting_them(self):
        notes_root = self.data/'Apuntes'
        (notes_root/'.glosa-eliminados').mkdir(parents=True, exist_ok=True)
        (notes_root/'.glosa-eliminados'/'viejo.md').write_text('# Viejo\n\nborrado viejo\n', encoding='utf-8')
        (notes_root/'.glosa-conflictos').mkdir(parents=True, exist_ok=True)
        (notes_root/'.glosa-conflictos'/'dup.md').write_text('# Dup\n\nconflicto viejo\n', encoding='utf-8')
        bundle = self.path/'bundle-recovery'
        export_room(bundle, self.data, self.root)
        self.assertTrue((bundle/'apuntes/originales/.glosa-eliminados/viejo.md').is_file())
        self.assertTrue((bundle/'apuntes/originales/.glosa-conflictos/dup.md').is_file())
        output, root = self.path/'restored-recovery', self.path/'new-root-recovery'
        root.mkdir()
        restore_room(bundle, output, root)
        self.assertTrue((output/'Apuntes/.glosa-eliminados/viejo.md').is_file())
        self.assertTrue((output/'Apuntes/.glosa-conflictos/dup.md').is_file())
        with workspace(root, output):
            state = server.snapshot()
        self.assertEqual([n for n in state['library']['notes']
                          if 'borrado viejo' in n['content'] or 'conflicto viejo' in n['content']], [])

    def test_local_credentials_stay_out_of_portable_backup(self):
        server.llm_providers.save_credential(self.data/'tutor-credentials.json','openrouter',
                                             server.llm_providers.PROVIDERS['openrouter']['baseUrl'],'backup-test-secret')
        bundle=self.path/'without-credentials'
        export_room(bundle,self.data,self.root)
        self.assertFalse((bundle/'tutor-credentials.json').exists())
        for file in bundle.rglob('*'):
            if file.is_file():
                self.assertNotIn(b'backup-test-secret',file.read_bytes())

    def test_corrupt_file_rejected_before_install(self):
        (self.bundle/'snapshot.json').write_text('{}')
        destination = self.path/'restored'
        with self.assertRaisesRegex(ValueError, 'alterado'):
            restore_room(self.bundle, destination, self.root)
        self.assertFalse(destination.exists())

    def test_manifest_traversal_and_symlinks_rejected(self):
        manifest = json.loads((self.bundle/'manifest.json').read_text())
        manifest['files']['root/sources/../../bad.pdf']={'bytes':0,'sha256':'0'*64}
        (self.bundle/'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Ruta'):
            verify_bundle(self.bundle)
        del manifest['files']['root/sources/../../bad.pdf']
        (self.bundle/'manifest.json').write_text(json.dumps(manifest))
        (self.bundle/'snapshot.json').rename(self.path/'original.json')
        (self.bundle/'snapshot.json').symlink_to(self.path/'original.json')
        with self.assertRaisesRegex(ValueError, 'simbólico'):
            verify_bundle(self.bundle)

    def test_zip_traversal_rejected(self):
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, 'w') as z:
            z.writestr('../escape', 'bad')
        with self.assertRaisesRegex(ValueError, 'Ruta'):
            rooms.import_zip(base64.b64encode(raw.getvalue()).decode(), self.data, self.root)
        self.assertFalse((self.path/'escape').exists())

    def test_two_rooms_with_same_ids_are_isolated_over_http(self):
        first = rooms.register(self.bundle, self.data, self.root, 'Primera')
        second = rooms.register(self.bundle, self.data, self.root, 'Segunda')
        old = server.DATA, server.DB, server.PORT
        server.DATA, server.DB = self.data, self.data/'learning.sqlite3'
        http = server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        server.PORT=http.server_address[1]
        threading.Thread(target=http.serve_forever,daemon=True).start()
        base='http://127.0.0.1:'+str(server.PORT)
        def request(room_id, path='/api/state', body=None):
            req=Request(base+path, data=json.dumps(body).encode() if body else None,
                        headers={'X-Glosa-Room':room_id,'Content-Type':'application/json'})
            with urlopen(req) as result:return json.load(result)
        try:
            request(first['id'],'/api/event',{'id':'only-first','kind':'visit','courseId':self.course_id,
                    'lessonId':self.lesson_id,'data':{'courseVersion':self.course_version}})
            with ThreadPoolExecutor(max_workers=4) as pool:
                results=list(pool.map(request,[first['id'],second['id']]*10))
            for index, result in enumerate(results):
                self.assertEqual('only-first' in {e['id'] for e in result['events']},index%2==0)
            with self.assertRaises(HTTPError):request('missing')
            downloaded=urlopen(Request(base+'/api/rooms/export',headers={'X-Glosa-Room':first['id']})).read()
            third=rooms.import_zip(base64.b64encode(downloaded).decode(),self.data,self.root,'Tercera')
            self.assertEqual(len(request(third['id'])['events']),2)
        finally:
            http.shutdown();http.server_close()
            server.DATA,server.DB,server.PORT=old


    def test_inventory_summarizes_vault_contents_read_only(self):
        item = rooms.register(self.bundle, self.data, self.root, 'Con contenido')
        folder = Path(item['path'])
        (folder/'assets'/'sources').mkdir(parents=True, exist_ok=True)
        (folder/'assets'/'sources'/'fuente.pdf').write_bytes(b'%PDF-1.4 temporal')
        scope = rooms.room(self.data, self.root, item['id'])
        with workspace(scope['root'], scope['data']):
            server.event('chat_message', self.course_id, self.lesson_id, {'text': 'Duda'}, 'chat-1')
            server.event('tutor_reply', self.course_id, self.lesson_id, {'text': 'Ayuda'}, 'tutor-1')
        entry = next(p for p in rooms.inventory(self.data, self.root)['pliegos'] if p['id'] == item['id'])
        self.assertEqual(entry['contents'], {'courses': 1, 'documents': 0, 'notes': 1,
                                             'events': 3, 'conversation': 2})
        self.assertEqual(entry['files']['pdfs'], 1)
        self.assertGreater(entry['files']['bytes'], 0)
        self.assertIsInstance(entry['modified'], float)
        # Summaries must not write sidecar files next to a live database.
        self.assertFalse((scope['data']/'learning.sqlite3-wal').exists())
        self.assertFalse((scope['data']/'learning.sqlite3-shm').exists())
        brief = next(p for p in rooms.inventory(self.data, self.root, details=False)['pliegos'] if p['id'] == item['id'])
        self.assertNotIn('contents', brief)
        self.assertNotIn('files', brief)

    def test_inventory_summary_survives_unreadable_database(self):
        item = rooms.create(self.data, self.root, 'Frágil')
        folder = rooms.room(self.data, self.root, item['id'])['data'].parent
        (folder/'learning'/'learning.sqlite3').write_bytes(b'no soy sqlite')
        entry = next(p for p in rooms.inventory(self.data, self.root)['pliegos'] if p['id'] == item['id'])
        self.assertIsNone(entry['contents'])
        self.assertEqual(entry['files']['pdfs'], 0)

    def test_rename_moves_the_folder_and_keeps_ids_and_history(self):
        item = rooms.register(self.bundle, self.data, self.root, 'Original')
        old_folder = rooms.room(self.data, self.root, item['id'])['data'].parent
        renamed = rooms.rename(self.data, self.root, item['id'], 'Renombrada')
        self.assertEqual(renamed['id'], item['id'])
        self.assertEqual(renamed['title'], 'Renombrada')
        # The visible folder follows the title; the ID and the data stay put.
        self.assertEqual(Path(renamed['path']).name, 'Renombrada')
        self.assertNotEqual(renamed['path'], str(old_folder))
        self.assertFalse(old_folder.exists())
        self.assertTrue((Path(renamed['path'])/'learning/learning.sqlite3').is_file())
        scope = rooms.room(self.data, self.root, item['id'])
        self.assertEqual(scope['title'], 'Renombrada')
        listing = {p['id']: p for p in rooms.inventory(self.data, self.root)['pliegos']}
        self.assertEqual(listing[item['id']]['title'], 'Renombrada')
        self.assertEqual(listing[item['id']]['path'], renamed['path'])
        stored = json.loads((self.data/'rooms.json').read_text())
        self.assertEqual([(entry['id'], entry['title']) for entry in stored], [(item['id'], 'Renombrada')])
        self.assertEqual(stored[0]['path'], renamed['path'])
        with workspace(scope['root'], scope['data']):
            state = server.snapshot()
            self.assertEqual([e['id'] for e in state['events']], ['trace-1'])
            self.assertEqual(state['library']['notes'][0]['content'], 'Texto persistente')

    def test_rename_updates_legacy_registry_title(self):
        item = rooms.create(self.data, self.root, 'Anterior')
        folder = rooms.room(self.data, self.root, item['id'])['data'].parent
        legacy = self.data/'rooms'/item['id']
        legacy.parent.mkdir()
        folder.rename(legacy)
        (legacy/'pliego.json').unlink()
        (self.data/'rooms.json').write_text(json.dumps([item]))
        renamed = rooms.rename(self.data, self.root, item['id'], 'Actualizada')
        self.assertEqual(renamed['title'], 'Actualizada')
        self.assertEqual(rooms.room(self.data, self.root, item['id'])['title'], 'Actualizada')
        self.assertFalse((legacy/'pliego.json').exists())

    def test_rename_rejects_invalid_targets_and_titles(self):
        item = rooms.create(self.data, self.root, 'Única')
        for room_id in ('local', rooms.TUTORIAL_ID, 'pliego-ausente', None):
            with self.subTest(room_id=room_id), self.assertRaises(ValueError):
                rooms.rename(self.data, self.root, room_id, 'Válida')
        for title in ('', '   ', None, 7, 'x'*201):
            with self.subTest(title=title), self.assertRaises(ValueError):
                rooms.rename(self.data, self.root, item['id'], title)
        self.assertEqual(rooms.room(self.data, self.root, item['id'])['title'], 'Única')
        self.assertFalse((self.data/'rooms.json').exists())


class LocalRetiredTests(unittest.TestCase):
    """Retiro de la biblioteca local por instalación (flag local-retired.json).

    Todo vive en temporales: nunca se toca una base ni un Margen reales. Sin el
    flag se conserva el comportamiento histórico; con el flag la biblioteca
    local se resuelve como el tutorial y deja de listarse.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='glosa-retired-')
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.data, self.root, self.home = base/'data', base/'root', base/'home'
        self.data.mkdir(); self.root.mkdir(); self.home.mkdir()
        (self.root/'courses').mkdir()
        shutil.copyfile(server.ROOT/'courses/tutorial.json', self.root/'courses/tutorial.json')
        env = patch.dict('os.environ', {'HOME': str(self.home)})
        env.start(); self.addCleanup(env.stop)
        margen = os.environ.pop('GLOSA_MARGEN_DIR', None)
        self.addCleanup(lambda: margen is not None and os.environ.__setitem__('GLOSA_MARGEN_DIR', margen))
        self.old = (server.DATA, server.DB, server.ROOT)
        server.DATA, server.DB, server.ROOT = self.data, self.data/'learning.sqlite3', self.root
        self.addCleanup(self._restore_server)

    def _restore_server(self):
        server.DATA, server.DB, server.ROOT = self.old

    def _retire(self, **overrides):
        info = {'format': 'glosa-local-retired', 'version': 1, 'retired': True}
        info.update(overrides)
        (self.data/rooms.LOCAL_RETIRED_FILE).write_text(json.dumps(info))

    def test_without_flag_local_is_kept(self):
        self.assertFalse(rooms.local_retired(self.data))
        self.assertIn('local', [item['id'] for item in rooms.list_rooms(self.data, self.root)])
        self.assertEqual(rooms.room(self.data, self.root, 'local')['data'], self.data)

    def test_retired_flag_hides_local_from_list_and_inventory(self):
        # A broken alias marker would warn without the flag; with it, it is moot.
        (self.data/rooms.LOCAL_ALIAS_FILE).write_text(json.dumps(
            {'format': 'glosa-local-alias', 'version': 1, 'id': 'local', 'path': str(self.home/'nada')}))
        self._retire()
        self.assertTrue(rooms.local_retired(self.data))
        ids = [item['id'] for item in rooms.list_rooms(self.data, self.root)]
        self.assertNotIn('local', ids)
        self.assertIn(rooms.TUTORIAL_ID, ids)
        listing = rooms.inventory(self.data, self.root)
        self.assertNotIn('local', listing)
        self.assertFalse(any('biblioteca local' in warning.lower() for warning in listing['warnings']))

    def test_retired_local_resolves_to_tutorial_without_touching_old_db(self):
        legacy = self.data/'learning.sqlite3'
        legacy.write_bytes(b'legacy-local-db')
        self._retire()
        scope = rooms.room(self.data, self.root, 'local')
        self.assertEqual(scope['id'], rooms.TUTORIAL_ID)
        self.assertEqual(scope['kind'], 'tutorial')
        self.assertEqual(scope['data'], self.data/'tutorial')
        self.assertEqual(legacy.read_bytes(), b'legacy-local-db')  # ni recreada ni abierta

    def test_server_defaults_resolve_tutorial_when_retired(self):
        legacy = self.data/'learning.sqlite3'
        legacy.write_bytes(b'legacy-local-db')
        self._retire()
        alias = server.local_alias()
        self.assertIsNotNone(alias)
        self.assertEqual(alias['id'], rooms.TUTORIAL_ID)
        self.assertEqual(server.active_workspace()['id'], rooms.TUTORIAL_ID)
        self.assertEqual(Path(server.library().db), self.data/'tutorial'/'learning.sqlite3')
        with server.connect() as conn:
            conn.execute('SELECT 1').fetchone()
        self.assertEqual(legacy.read_bytes(), b'legacy-local-db')

    def test_retired_flag_can_be_paused_without_deleting_file(self):
        self._retire(retired=False)
        self.assertFalse(rooms.local_retired(self.data))
        self.assertIn('local', [item['id'] for item in rooms.list_rooms(self.data, self.root)])

    def test_api_redirects_retired_local_to_tutorial(self):
        self._retire()
        old_port = server.PORT
        http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        server.PORT = http.server_address[1]
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()

        def stop():
            http.shutdown(); http.server_close(); thread.join(timeout=2); server.PORT = old_port

        self.addCleanup(stop)
        base = 'http://127.0.0.1:'+str(server.PORT)
        with urlopen(Request(base+'/api/state', headers={'X-Glosa-Room': 'local'}), timeout=10) as response:
            self.assertEqual(response.headers.get('X-Glosa-Room-Redirect'), rooms.TUTORIAL_ID)
            state = json.load(response)
        self.assertEqual(state['room']['id'], rooms.TUTORIAL_ID)
        with urlopen(Request(base+'/api/rooms', headers={'X-Glosa-Room': 'local'}), timeout=10) as response:
            listing = json.load(response)
        self.assertNotIn('local', [item['id'] for item in listing['rooms']])


if __name__ == '__main__':
    unittest.main()
