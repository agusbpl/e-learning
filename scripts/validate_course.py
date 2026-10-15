"""Validate an authored course without changing the student's database."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import validate_course

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Uso: python3 scripts/validate_course.py archivo.json')
    try:
        course = validate_course(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise SystemExit('Curso inválido: ' + str(exc))
    print('%s: %s lecciones; estructura válida.' % (course['title'], len(course['lessons'])))
