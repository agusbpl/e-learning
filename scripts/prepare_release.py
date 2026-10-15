"""Build a reviewable public source tree without private data or Git history.

Uses release-files.json, never git archive. This is a content filter, not a
guarantee of ownership or a replacement for reviewing the resulting files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {'.git', '.local-data', '.aws', '.codex', '.agents',
                   'node_modules', '__pycache__', '.venv', '.venv-author',
                   'sources', 'source-archives', '.md_cache', 'output',
                   'backups', 'exports', 'recordings', 'media'}
SECRET_PATTERNS = (
    re.compile(rb'\bsk-(?:proj-|or-v1-)?[A-Za-z0-9_-]{24,}\b'),
    re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),
    re.compile(rb'\bgithub_pat_[A-Za-z0-9_]{30,}\b'),
    re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
)


def safe_relative(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or '..' in path.parts or '\\' in name
            or path.as_posix() != name or any(p in FORBIDDEN_PARTS for p in path.parts)
            or any(p.startswith('.env') for p in path.parts)
            or any(p.startswith('tutor-credentials') for p in path.parts)
            or path.suffix in {'.sqlite3', '.db', '.log', '.zip', '.pdf', '.mp4', '.jpg'}):
        raise ValueError('Ruta no distribuible en la lista de release')
    return path


def validate_bytes(data: bytes, name: str, private_home: Path) -> None:
    # Never display a matched secret or the person's home directory.
    if any(pattern.search(data) for pattern in SECRET_PATTERNS):
        raise ValueError('Posible secreto en ' + name + '; revisar localmente (valor omitido)')
    home = str(private_home).encode()
    if home not in (b'/', b'/root') and home in data:
        raise ValueError('Ruta personal en ' + name + '; revisar localmente (valor omitido)')


def prepare(source: Path, output: Path, private_home: Path | None = None) -> dict:
    source, output = source.resolve(), output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('El destino debe ser nuevo; no se sobrescriben archivos')
    resolved_output = output.resolve()
    if resolved_output.is_relative_to(source):
        raise ValueError('Usá un destino fuera del árbol de trabajo')
    policy = json.loads((source / 'release-files.json').read_text(encoding='utf-8'))
    names = policy['files']
    if not isinstance(names, list) or not names or len(names) != len(set(names)):
        raise ValueError('Lista de archivos inválida o duplicada')
    private_home = private_home or Path.home()
    files = []
    # Validate everything before writing the candidate.
    for name in sorted(names):
        relative = safe_relative(name)
        path = source.joinpath(*relative.parts)
        if any(parent.is_symlink() for parent in (path, *path.parents) if parent != source.parent):
            raise ValueError('Enlace simbólico no distribuible: ' + name)
        if not path.is_file() or not path.resolve().is_relative_to(source):
            raise ValueError('Archivo de release ausente o fuera del árbol: ' + name)
        data = path.read_bytes()
        validate_bytes(data, name, private_home)
        files.append((name, data, path.stat().st_mode & 0o111))
    manifest = {'format': 'glosa-public-source', 'version': 1,
                'historyIncluded': False,
                'files': {name: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
                          for name, data, _ in files}}
    with tempfile.TemporaryDirectory(prefix='glosa-release-stage-', dir=output.parent) as stage_dir:
        stage = Path(stage_dir) / 'source'
        stage.mkdir()
        for name, data, executable in files:
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o755 if executable else 0o644)
        (stage / 'RELEASE_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        # Recheck just before publishing this local candidate.
        if output.exists() or output.is_symlink():
            raise ValueError('El destino apareció durante la preparación')
        shutil.move(str(stage), str(output))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='Directorio nuevo fuera del proyecto; no publica ni crea commits')
    args = parser.parse_args()
    try:
        manifest = prepare(ROOT, args.output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')
    print(f'Candidato local preparado: {len(manifest["files"])} archivos; sin historial Git.')
    print('Revisá RELEASE_MANIFEST.json y ejecutá las pruebas desde ese directorio antes de publicar.')


if __name__ == '__main__':
    main()
