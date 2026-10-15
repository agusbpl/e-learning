#!/usr/bin/env bash
set -euo pipefail
study_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
study_runtime="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
exec "$study_root/.local-data/tailscale/bin/tailscale" \
  --socket="$study_runtime/estudio-tailscale/tailscaled.sock" "$@"
