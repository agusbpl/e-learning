#!/usr/bin/env bash
set -euo pipefail
study_root="$(cd -- "$(dirname -- "$0")" && pwd)"
exec "$study_root/.venv-author/bin/python" "$study_root/tutor_mcp.py"
