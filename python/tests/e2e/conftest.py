"""E2E fixtures: поднимаем docker-infra + все микросервисы при необходимости."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
START_ALL = REPO_ROOT / "scripts" / "start_all.sh"
COMPOSE_FILE = REPO_ROOT / "infra" / "docker-compose.yml"
GATEWAY_URL = os.environ.get("CITYVIBE_E2E_GATEWAY", "http://127.0.0.1:8080")
MAILHOG_URL = os.environ.get("CITYVIBE_E2E_MAILHOG", "http://127.0.0.1:8025")
PYTHON = os.environ.get(
    "PYTHON",
    "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
)

HEALTH_URLS = {
    "gateway": f"{GATEWAY_URL}/health",
    "user": "http://127.0.0.1:8081/health",
    "auth": "http://127.0.0.1:8082/health",
    "place": "http://127.0.0.1:8083/health",
    "notification": "http://127.0.0.1:8084/health",
    "design": "http://127.0.0.1:8085/health",
    "milana": "http://127.0.0.1:8086/health",
}


def _http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        r = httpx.get(url, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _gateway_backends_ok() -> bool:
    try:
        r = httpx.get(HEALTH_URLS["gateway"], timeout=3.0)
        if r.status_code != 200:
            return False
        data = r.json()
        if data.get("gateway") != "ok":
            return False
        backends = data.get("backends") or {}
        required = ("auth", "users", "places")
        return all(backends.get(k) == "ok" for k in required)
    except Exception:
        return False


def _all_services_healthy() -> bool:
    if not _gateway_backends_ok():
        return False
    return all(_http_ok(url) for name, url in HEALTH_URLS.items() if name != "gateway")


def _docker_available() -> bool:
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
            timeout=20,
        )
        return True
    except Exception:
        return False


def _ensure_infra() -> None:
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d"],
        cwd=str(REPO_ROOT),
        check=True,
        timeout=180,
    )
    deadline = time.time() + 90
    while time.time() < deadline:
        if _http_ok("http://127.0.0.1:8025/api/v2/messages") and _redis_ping():
            # postgres: через docker exec
            if _postgres_ready():
                return
        time.sleep(1)
    raise RuntimeError("Infra (postgres/redis/mailhog) не поднялась вовремя")


def _redis_ping() -> bool:
    try:
        r = subprocess.run(
            ["docker", "exec", "cityvibe-redis", "redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0 and "PONG" in (r.stdout or "")
    except Exception:
        return False


def _postgres_ready() -> bool:
    try:
        r = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "exec",
                "-T",
                "postgres",
                "pg_isready",
                "-U",
                "cityvibe",
                "-d",
                "cityvibe_users",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            timeout=15,
        )
        return r.returncode == 0
    except Exception:
        return False


def _migrate_and_seed() -> None:
    """Идемпотентные миграции + seed городов (нужен city_id для register)."""
    env = os.environ.copy()
    env["PYTHON"] = PYTHON
    subprocess.run(
        ["make", "migrate-all", "seed-place"],
        cwd=str(REPO_ROOT),
        check=True,
        timeout=180,
        env=env,
    )


def _start_microservices() -> None:
    if not START_ALL.is_file():
        raise RuntimeError(f"Не найден {START_ALL}")
    START_ALL.chmod(START_ALL.stat().st_mode | 0o111)
    subprocess.run(
        ["bash", str(START_ALL)],
        cwd=str(REPO_ROOT),
        check=True,
        timeout=180,
        start_new_session=True,
    )


def _wait_healthy(timeout_sec: float = 120.0) -> None:
    deadline = time.time() + timeout_sec
    last_missing: list[str] = []
    while time.time() < deadline:
        missing = [name for name, url in HEALTH_URLS.items() if not _http_ok(url)]
        if not missing and _gateway_backends_ok():
            return
        last_missing = missing
        time.sleep(1)
    raise RuntimeError(f"Сервисы не стали healthy: missing={last_missing}")


@pytest.fixture(scope="session")
def live_backend():
    """
    Гарантирует живой backend-стек (infra + микросервисы + gateway).
    Не останавливает процессы после теста — локальная среда остаётся рабочей.
    """
    if not _docker_available():
        pytest.skip("Docker недоступен — e2e пропущен")

    if not _all_services_healthy():
        _ensure_infra()
        _migrate_and_seed()
        _start_microservices()
        _wait_healthy()

    yield {
        "gateway": GATEWAY_URL.rstrip("/"),
        "mailhog": MAILHOG_URL.rstrip("/"),
        "repo_root": REPO_ROOT,
        "compose_file": COMPOSE_FILE,
    }
