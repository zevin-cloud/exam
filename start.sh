#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

mkdir -p "$RUN_DIR"

stop_pid_file() {
  local name="$1"
  local pid_file="$RUN_DIR/$name.pid"
  if [[ ! -f "$pid_file" ]]; then return; fi
  local pid
  pid="$(tr -d '[:space:]' < "$pid_file")"
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    for _ in {1..20}; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.1
    done
    if kill -0 "$pid" 2>/dev/null; then kill -9 "$pid"; fi
    echo "[$name] stopped (PID: $pid)"
  fi
  rm -f "$pid_file"
}

port_is_busy() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
  elif command -v ss >/dev/null 2>&1; then
    ss -ltn | awk '{print $4}' | grep -Eq "(^|:)$port$"
  else
    return 1
  fi
}

stop_services() {
  stop_pid_file frontend
  stop_pid_file backend
}

if [[ "${1:-}" == "stop" ]]; then
  stop_services
  exit 0
fi

stop_services
for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
  if port_is_busy "$port"; then
    echo "[Error] Port $port is occupied by a process not managed by this script." >&2
    echo "Set BACKEND_PORT/FRONTEND_PORT to free ports, or stop the occupying process first." >&2
    exit 1
  fi
done

if [[ ! -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  echo "[Setup] Creating Python virtual environment..."
  python3 -m venv "$BACKEND_DIR/.venv"
  "$BACKEND_DIR/.venv/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "[Setup] Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
fi

(
  cd "$BACKEND_DIR"
  nohup .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload \
    >"$RUN_DIR/backend.log" 2>&1 &
  echo $! >"$RUN_DIR/backend.pid"
)

(
  cd "$FRONTEND_DIR"
  nohup env VITE_API_PROXY_TARGET="http://127.0.0.1:$BACKEND_PORT" \
    npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" \
    >"$RUN_DIR/frontend.log" 2>&1 &
  echo $! >"$RUN_DIR/frontend.pid"
)

sleep 3
for name in backend frontend; do
  pid="$(cat "$RUN_DIR/$name.pid")"
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "[Error] $name failed to start. See $RUN_DIR/$name.log" >&2
    exit 1
  fi
done

echo "[Backend] http://127.0.0.1:$BACKEND_PORT (PID: $(cat "$RUN_DIR/backend.pid"))"
echo "[Frontend] http://127.0.0.1:$FRONTEND_PORT (PID: $(cat "$RUN_DIR/frontend.pid"))"
echo "[Logs] $RUN_DIR"
