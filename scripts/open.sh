#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
data_dir="${LEARNING_DATA_DIR:-$root/.local-data}"
url="http://localhost:${LEARNING_PORT:-8765}/"
mkdir -p -- "$data_dir"
log="$data_dir/glosa-server.log"

ready() {
    curl --noproxy '*' --fail --silent --output /dev/null --max-time 1 "$url"
}

# Serialize launches so repeated shortcuts do not start duplicate servers.
exec 9>"$data_dir/glosa-launch.lock"
flock 9
if ! ready; then
    nohup "$root/start.sh" </dev/null >>"$log" 2>&1 9>&- &
    server_pid=$!
    for ((attempt = 0; attempt < 100; attempt++)); do
        ready && break
        kill -0 "$server_pid" 2>/dev/null || break
        sleep 0.1
    done
    if ! ready; then
        message="Glosa no pudo iniciar. Revisá $log"
        printf '%s\n' "$message" >&2
        if command -v notify-send >/dev/null; then
            notify-send 'Glosa' "$message" || true
        fi
        exit 1
    fi
fi
flock -u 9
exec 9>&-

# Qtile passes its existing browser command; direct launches use the default browser.
if (($#)); then
    exec "$@"
fi
exec xdg-open "$url"
