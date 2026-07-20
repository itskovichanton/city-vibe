"""Integration tests (testcontainers: Postgres + Redis)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON_ROOT = Path(__file__).resolve().parents[2]
AUTH_SRC = PYTHON_ROOT / "auth_service" / "src"
SITE = Path("/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages")

for p in (REPO_ROOT, AUTH_SRC, SITE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from python.auth_service.src.auth_service.entities.common import RegisterRequest, VerifyOtpRequest
from python.auth_service.src.auth_service.infra.jwt_service import JwtServiceImpl
from python.auth_service.src.auth_service.infra.otp_store import OtpChallenge, RedisAuthOtpStore
from python.auth_service.src.auth_service.infra.password import PasswordServiceImpl
from python.auth_service.src.auth_service.repo.account import AccountRepoImpl
from python.auth_service.src.auth_service.usecase.auth_flow import AuthUseCaseImpl
from python.libs.clients.db import Database
from python.libs.infra.redis_client import RedisClientImpl


def _docker_available() -> bool:
    try:
        import docker

        docker.from_env().ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def containers():
    if not _docker_available():
        pytest.skip("Docker недоступен — integration tests пропущены")
    from testcontainers.postgres import PostgresContainer
    from testcontainers.redis import RedisContainer

    pg = PostgresContainer("postgres:16-alpine")
    redis = RedisContainer("redis:7-alpine")
    try:
        pg.start()
        redis.start()
        yield {
            "pg_url": pg.get_connection_url().replace("psycopg2", "asyncpg"),
            "pg_sync_url": pg.get_connection_url(),
            "redis_host": redis.get_container_host_ip(),
            "redis_port": int(redis.get_exposed_port(6379)),
        }
    except Exception as exc:
        pytest.skip(f"Testcontainers недоступны: {exc}")
    finally:
        redis.stop()
        pg.stop()


@pytest.fixture(scope="module")
def auth_stack(containers, event_loop):
    migrations_dir = PYTHON_ROOT / "auth_service" / "sql" / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))

    async def _setup():
        import psycopg2

        sync_url = containers["pg_sync_url"].replace("postgresql+psycopg2://", "postgresql://")
        conn = psycopg2.connect(sync_url)
        conn.autocommit = True
        cur = conn.cursor()
        for sql_file in sql_files:
            cur.execute(sql_file.read_text(encoding="utf-8"))
        cur.close()
        conn.close()

        db = Database()
        db.url = containers["pg_url"]
        db.echo = False
        db.pool_size = 3
        db.init()
        from sqlalchemy import text

        async with db.engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        redis = RedisClientImpl()
        redis._url = f"redis://{containers['redis_host']}:{containers['redis_port']}/0"
        redis.init()

        account_repo = object.__new__(AccountRepoImpl)
        account_repo.db = db

        otp_store = RedisAuthOtpStore()
        otp_store.redis_client = redis
        otp_store.otp_ttl_sec = 300
        otp_store.init()

        jwt_svc = JwtServiceImpl()
        jwt_svc.jwt_secret = "integration-test-secret"
        jwt_svc.access_ttl_min = 15
        jwt_svc.refresh_ttl_days = 30
        jwt_svc.init()

        cfg = MagicMock()
        cfg.get_config.return_value = MagicMock(
            settings={"auth": {"google_client_ids": []}}
        )

        uc = AuthUseCaseImpl()
        uc.account_repo = account_repo
        uc.password_service = PasswordServiceImpl()
        uc.jwt_service = jwt_svc
        uc.otp_store = otp_store
        uc.outbox = AsyncMock()
        uc.user_client = MagicMock()
        uc.user_client.create_user.return_value = {"id": 1001}
        uc.user_client.delete_user = MagicMock()
        uc.config_service = cfg
        uc.otp_ttl_sec = 300
        uc.init(otp_ttl_sec=300)
        return uc, redis

    return event_loop.run_until_complete(_setup())


@pytest.mark.asyncio
async def test_register_otp_verify_integration(auth_stack):
    uc, redis = auth_stack
    challenge = await uc.register(
        RegisterRequest(
            name="Integration User",
            identifier="integration@test.local",
            password="SecurePass1!",
            birthdate=None,
            city_id=1,
            accept_terms=True,
        )
    )
    assert challenge.challenge_id
    stored = await uc.otp_store.get(challenge.challenge_id)
    assert stored is not None
    assert len(stored.code) == 6

    tokens = await uc.register_verify(
        VerifyOtpRequest(challenge_id=challenge.challenge_id, code=stored.code)
    )
    assert tokens.access_token
    assert tokens.user_id == 1001
    uc.user_client.create_user.assert_called_once()
