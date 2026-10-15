import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.prepare_release import prepare


class PublicReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='glosa-release-test-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / 'private-workspace'
        self.source.mkdir()
        (self.source / 'app.py').write_text('print("hello")\n')
        self.output = self.base / 'candidate'
        self.policy(['app.py'])

    def policy(self, files):
        (self.source / 'release-files.json').write_text(json.dumps({'files': files}))

    def test_only_allowlisted_files_and_hashes_are_distributed(self):
        (self.source / '.git').mkdir()
        (self.source / '.git/config').write_text('PRIVATE REMOTE')
        (self.source / '.env').write_text('PRIVATE API')
        (self.source / 'study.pdf').write_bytes(b'PRIVATE STUDY')
        manifest = prepare(self.source, self.output)
        self.assertEqual(set(p.name for p in self.output.iterdir()), {'app.py', 'RELEASE_MANIFEST.json'})
        self.assertEqual(manifest['files']['app.py']['sha256'],
                         hashlib.sha256((self.output / 'app.py').read_bytes()).hexdigest())
        self.assertEqual((self.source / '.env').read_text(), 'PRIVATE API')

    def test_refuses_private_paths_and_path_traversal(self):
        for path in ('.git/config', '../app.py', '/tmp/app.py', '.env', 'sources/book.pdf',
                     '.local-data/state.json', 'web/media/movie.mp4', 'tutor-credentials.json'):
            with self.subTest(path=path):
                self.policy([path])
                with self.assertRaises(ValueError):
                    prepare(self.source, self.output)
                self.assertFalse(self.output.exists())

    def test_refuses_file_and_parent_symlinks(self):
        outside = self.base / 'private'
        outside.mkdir()
        (outside / 'secret.txt').write_text('PRIVATE')
        for link, target, entry in [('file.txt', outside / 'secret.txt', 'file.txt'),
                                    ('linked', outside, 'linked/secret.txt')]:
            (self.source / link).symlink_to(target)
            self.policy([entry])
            with self.assertRaises(ValueError):
                prepare(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_detects_secrets_and_personal_paths_without_echoing_values(self):
        for content in ('sk-' + 'a' * 32, '/home/private-person/docs/file.txt'):
            (self.source / 'app.py').write_text(content)
            with self.assertRaises(ValueError) as caught:
                prepare(self.source, self.output, Path('/home/private-person'))
            self.assertNotIn(content, str(caught.exception))
            self.assertFalse(self.output.exists())

    def test_refuses_overwriting_or_nested_output(self):
        self.output.mkdir()
        (self.output / 'keep').write_text('KEEP')
        with self.assertRaises(ValueError):
            prepare(self.source, self.output)
        with self.assertRaises(ValueError):
            prepare(self.source, self.source / 'candidate')
        self.assertEqual((self.output / 'keep').read_text(), 'KEEP')


if __name__ == '__main__':
    unittest.main()
