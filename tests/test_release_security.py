"""Loopback regression checks for provider redirects and malformed POST bodies."""
import json
import base64
import io
import os
from pathlib import Path
import tempfile
import threading
import unittest
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib import error, request


class ReleaseSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data = Path(self.temporary.name)
        with patch.dict(os.environ, {'LEARNING_DATA_DIR': str(self.data), 'OPENROUTER_API_KEY': ''}):
            import server
        self.server_module = server
        self.running = []
        self.addCleanup(self.stop_servers)

    def start_server(self, handler):
        http = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        self.running.append((http, thread))
        return f'http://127.0.0.1:{http.server_port}'

    def stop_servers(self):
        for http, thread in self.running:
            http.shutdown()
            http.server_close()
            thread.join(timeout=2)

    def test_authenticated_provider_redirect_does_not_reach_other_origin(self):
        received = []

        class Target(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                received.append(self.headers.get('Authorization'))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{}')

        target = self.start_server(Target)

        class Redirect(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.send_response(302)
                self.send_header('Location', target + '/capture')
                self.end_headers()

        origin = self.start_server(Redirect)
        server = self.server_module
        with patch.object(server, 'provider_key', return_value='dummy-test-key'):
            with self.assertRaises(ValueError) as caught:
                server.provider_request({'provider': 'freellmapi', 'providerBaseUrl': origin}, 'models')
        self.assertIn('HTTP 302', str(caught.exception))
        self.assertEqual(received, [])

        # OpenRouter uses a fixed public URL; substitute only the request target
        # so its own authenticated transport is exercised without external traffic.
        original_request = request.Request

        def local_request(url, *args, **kwargs):
            return original_request(url.replace('https://openrouter.ai/api/v1/', origin + '/'), *args, **kwargs)

        with patch.object(server.request, 'Request', side_effect=local_request):
            with patch.object(server, 'KEY', 'dummy-test-key'):
                with self.assertRaises(ValueError) as caught:
                    server.openrouter('models')
        self.assertIn('HTTP 302', str(caught.exception))
        self.assertEqual(received, [])

    def test_post_requires_json_object(self):
        server = self.server_module
        with patch.object(server.Handler, 'allowed', return_value=True), patch.object(
                server.rooms, 'room', return_value={'id': 'local', 'data': self.data, 'root': self.data}):
            origin = self.start_server(server.Handler)
            for value in ([], None, 5, 'text'):
                with self.subTest(value=value):
                    payload = json.dumps(value).encode()
                    req = request.Request(origin + '/api/margen', data=payload,
                                          headers={'Content-Type': 'application/json'})
                    with self.assertRaises(error.HTTPError) as caught:
                        request.urlopen(req, timeout=5)
                    self.assertEqual(caught.exception.code, 400)
                    with caught.exception:
                        self.assertIn('objeto JSON', json.load(caught.exception)['error'])

    def test_invalid_backup_location_and_manifest_are_client_errors(self):
        server = self.server_module
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.writestr('manifest.json', '[]')
        inputs = ({'folder': str(self.data / 'missing')},
                  {'folder': str(self.data)},
                  {'folder': str(self.data), 'title': 5},
                  {'base64': base64.b64encode(archive.getvalue()).decode()})
        with patch.object(server.Handler, 'allowed', return_value=True), patch.object(
                server.rooms, 'room', return_value={'id': 'local', 'data': self.data, 'root': self.data}):
            origin = self.start_server(server.Handler)
            for value in inputs:
                with self.subTest(value=value):
                    req = request.Request(origin + '/api/rooms/import', data=json.dumps(value).encode(),
                                          headers={'Content-Type': 'application/json'})
                    with self.assertRaises(error.HTTPError) as caught:
                        request.urlopen(req, timeout=5)
                    self.assertEqual(caught.exception.code, 400)
                    caught.exception.close()
        self.assertEqual(list(self.data.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
