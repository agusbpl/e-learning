"""Temporary workspaces only: portable backups and room isolation."""
import base64
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest
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


if __name__ == '__main__':
    unittest.main()
