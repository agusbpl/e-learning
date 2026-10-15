"""Video import validation without a server, student database or external requests."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server


class VideoResourceTests(unittest.TestCase):
    def setUp(self):
        self.course = json.loads((ROOT / 'courses/tutorial.json').read_text())
        self.video = {'kind': 'youtube', 'videoId': 'cfYl7Xhymx0',
                      'title': 'Un caso de transformación', 'task': 'Relacioná el cambio con el proceso.'}
        self.course['lessons'][0]['resources'] = [self.video]

    def test_supported_courses_and_optional_start(self):
        server.validate_course(self.course)
        for start in (0, 125):
            self.video['startSeconds'] = start
            server.validate_course(self.course)
        server.validate_course(json.loads((ROOT / 'courses/tutorial.json').read_text()))

    def test_malformed_resource_collections_are_rejected(self):
        for resources in (None, {}, 'youtube', [None], ['video'], [42]):
            with self.subTest(resources=resources):
                course = copy.deepcopy(self.course)
                course['lessons'][0]['resources'] = resources
                with self.assertRaises(ValueError):
                    server.validate_course(course)

    def test_video_id_and_author_metadata_are_required(self):
        invalid = [('kind', 'other'), ('videoId', 'é' * 11), ('videoId', 'too-short'),
                   ('videoId', 'https://youtu.be/cfYl7Xhymx0'), ('videoId', None)]
        invalid += [(field, value) for field in ('title', 'task') for value in ('', ' \n ', None, 5)]
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                course = copy.deepcopy(self.course)
                course['lessons'][0]['resources'][0][field] = value
                with self.assertRaises(ValueError):
                    server.validate_course(course)

    def test_invalid_start_seconds_are_rejected(self):
        for value in (-1, 1.5, True, '10', None, float('nan'), float('inf')):
            with self.subTest(value=value):
                self.video['startSeconds'] = value
                with self.assertRaises(ValueError):
                    server.validate_course(self.course)


if __name__ == '__main__':
    unittest.main()
