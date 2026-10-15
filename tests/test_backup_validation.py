"""Invalid local/ZIP backup input must fail without creating an imported room."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.room_backup import verify_bundle


class BackupInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='glosa-backup-input-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_missing_folder_or_manifest_is_an_input_error(self):
        for folder in (self.root / 'missing', self.root):
            with self.subTest(folder=folder), self.assertRaises(ValueError):
                verify_bundle(folder)

    def test_non_object_manifest_and_invalid_utf8_are_input_errors(self):
        for content in (b'[]', b'null', b'"text"', b'{', b'\xff'):
            (self.root / 'manifest.json').write_bytes(content)
            with self.subTest(content=content), self.assertRaises(ValueError):
                verify_bundle(self.root)

    def test_non_object_snapshot_and_invalid_file_metadata_are_rejected(self):
        snapshot = b'[]'
        (self.root / 'snapshot.json').write_bytes(snapshot)
        entry = {'bytes': len(snapshot), 'sha256': hashlib.sha256(snapshot).hexdigest()}
        manifest = {'format': 'glosa-workspace', 'version': 1,
                    'files': {'snapshot.json': entry}, 'courseIds': []}
        for metadata in (entry, {}, {'bytes': -1, 'sha256': 'x'}, None):
            manifest['files']['snapshot.json'] = metadata
            (self.root / 'manifest.json').write_text(json.dumps(manifest))
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                verify_bundle(self.root)


if __name__ == '__main__':
    unittest.main()
