"""Exact-origin access through a loopback-only Tailscale Serve proxy."""
from email.header import decode_header, make_header
import json
import re


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError('Configuración remota inválida.')
    origin = config.get('origin', '')
    if not isinstance(origin, str) or not re.fullmatch(
            r'https://[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.ts\.net', origin):
        raise ValueError('El acceso remoto requiere el nombre HTTPS exacto de Tailscale.')
    login = config.get('allowedLogin', '')
    if not isinstance(login, str) or not login.strip() or any(ord(c) < 32 for c in login):
        raise ValueError('Falta la identidad de la cuenta autorizada.')
    return {'origin': origin, 'allowedLogin': login}


def load_config(path):
    try:
        return validate_config(json.loads(path.read_text(encoding='utf-8')))
    except (OSError, ValueError):
        # Invalid or absent configuration never widens access.
        return None


def allowed(headers, port, config):
    for name in ('Host', 'Origin', 'Tailscale-User-Login', 'Tailscale-Funnel-Request'):
        if len(headers.get_all(name, [])) > 1:
            return False
    if headers.get('Tailscale-Funnel-Request'):
        return False
    host, origin = headers.get('Host', ''), headers.get('Origin')
    if host in (f'127.0.0.1:{port}', f'localhost:{port}'):
        return not origin or origin in (f'http://127.0.0.1:{port}', f'http://localhost:{port}')
    if not config or host not in (config['origin'][8:], config['origin'][8:] + ':443'):
        return False
    if origin and origin != config['origin']:
        return False
    try:
        login = str(make_header(decode_header(headers.get('Tailscale-User-Login', ''))))
    except (UnicodeError, LookupError, ValueError):
        return False
    # Serve removes caller-supplied identity headers and inserts the authenticated
    # account. This is trustworthy only because the backend binds to loopback.
    return login == config['allowedLogin']
