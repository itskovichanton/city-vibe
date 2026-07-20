#!/usr/bin/env bash
# Запуск всех микросервисов City Vibe в фоне + ожидание health.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-/Library/Frameworks/Python.framework/Versions/3.12/bin/python3}"
LOG_DIR="${ROOT}/.run/logs"
PID_DIR="${ROOT}/.run/pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

export PYTHONPATH="${ROOT}:${ROOT}/python/user_service/src:${ROOT}/python/auth_service/src:${ROOT}/python/place_catalog/src:${ROOT}/python/notification_service/src:${ROOT}/python/api_gateway/src:/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages"
export CITYVIBE_TRACING_ENABLED="${CITYVIBE_TRACING_ENABLED:-true}"
export CITYVIBE_OTEL_ENDPOINT="${CITYVIBE_OTEL_ENDPOINT:-http://localhost:4317}"

start_one() {
  local name="$1"
  local dir="$2"
  local port="$3"
  local otel_name="$4"
  local pidfile="${PID_DIR}/${name}.pid"
  local logfile="${LOG_DIR}/${name}.log"

  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "  already running: ${name} (pid $(cat "$pidfile"))"
    return 0
  fi

  echo "  starting ${name} → :${port} (otel=${otel_name})"
  (
    cd "$dir"
    export CITYVIBE_OTEL_SERVICE_NAME="$otel_name"
    exec "$PYTHON" main.py
  ) >"$logfile" 2>&1 &
  echo $! >"$pidfile"
}

wait_health() {
  local url="$1"
  local label="$2"
  local i=0
  until curl -sf "$url" >/dev/null 2>&1; do
    i=$((i + 1))
    if [[ $i -ge 60 ]]; then
      echo "TIMEOUT waiting for ${label} (${url})"
      echo "  log: ${LOG_DIR}/${label}.log"
      return 1
    fi
    sleep 1
  done
  echo "  ok ${label}"
}

echo "=== City Vibe: start all services ==="
start_one user          "${ROOT}/python/user_service"          8081 user-service
start_one auth          "${ROOT}/python/auth_service"          8082 auth-service
start_one place         "${ROOT}/python/place_catalog"         8083 place-catalog
start_one notification  "${ROOT}/python/notification_service"  8084 notification-service
start_one gateway       "${ROOT}/python/api_gateway"           8080 api-gateway

echo "=== waiting health ==="
wait_health "http://127.0.0.1:8081/health" user
wait_health "http://127.0.0.1:8082/health" auth
wait_health "http://127.0.0.1:8083/health" place
wait_health "http://127.0.0.1:8084/health" notification
wait_health "http://127.0.0.1:8080/health" gateway

echo ""
echo "Gateway:  http://localhost:8080"
echo "Jaeger:   http://localhost:16686"
echo "MailHog:  http://localhost:8025"
echo "Logs:     ${LOG_DIR}/"
echo "Stop:     make stop-all"
