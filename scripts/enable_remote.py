#!/usr/bin/env python3
"""Activate private HTTPS access after the owner links the computer."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from remote_access import validate_config


def main():
    cli = [str(ROOT / 'scripts/tailscale.sh')]
    status = json.loads(subprocess.check_output(cli + ['status', '--json'], text=True))
    if status.get('BackendState') != 'Running':
        print('Primero vinculá esta computadora a tu cuenta de Tailscale.')
        return 1
    node = status['Self']
    login = status.get('User', {}).get(str(node['UserID']), {}).get('LoginName')
    config = validate_config({'origin': 'https://' + node['DNSName'].rstrip('.'), 'allowedLogin': login})
    file = ROOT / '.local-data/remote-access.json'
    temp = file.with_suffix('.tmp')
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as output:
        json.dump(config, output, ensure_ascii=False)
    temp.replace(file)
    subprocess.run(['systemctl', '--user', 'start', 'estudio.service'], check=True)
    # The native CLI prints an approval link if HTTPS must first be enabled.
    # Do not enable Funnel: this service is private to the tailnet.
    result = subprocess.run(cli + ['serve', '--bg', '--https=443', 'http://127.0.0.1:8765'])
    if result.returncode:
        return result.returncode
    serve = json.loads(subprocess.check_output(cli + ['serve', 'status', '--json'], text=True))
    if any(serve.get('AllowFunnel', {}).values()):
        subprocess.run(cli + ['serve', 'reset'], check=True)
        raise ValueError('Se desactivó una configuración pública inesperada.')
    print('\nEnlace privado de estudio: ' + config['origin'])
    print('En Android, conectá Tailscale con la misma cuenta antes de abrirlo.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
