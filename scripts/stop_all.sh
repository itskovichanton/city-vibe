#!/usr/bin/env bash
# Остановка всех микросервисов, запущенных через start_all.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_DIR="${ROOT}/.run/pids"

if [[ ! -d "$PID_DIR" ]]; then
  echo "Нет pid-файлов — нечего останавливать"
  exit 0
fi

echo "=== City Vibe: stop all services ==="
for pidfile in "$PID_DIR"/*.pid; do
  [[ -f "$pidfile" ]] || continue
  name="$(basename "$pidfile" .pid)"
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  if [[ -n "${pid}" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "  stop ${name} (pid ${pid})"
    kill "$pid" 2>/dev/null || true
    # дочерние uvicorn/процессы
    sleep 0.3
    kill -9 "$pid" 2>/dev/null || true
  else
    echo "  already dead: ${name}"
  fi
  rm -f "$pidfile"
done
echo "OK"
