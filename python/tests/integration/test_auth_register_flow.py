"""Integration tests (testcontainers: Postgres + Redis) — полный auth flow."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON_ROOT = Path(__file__).resolve().parents[2]
AUTH_SRC = PYTHON_ROOT / "auth_service" / "src"
SITE = Path("/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages")

for p in (REPO_ROOT, AUTH_SRC, SITE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from python.auth_service.src.auth_service.entities.common import (  # noqa: E402
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyOtpRequest,
)
from python.auth_service.src.auth_service.infra.jwt_service import JwtServiceImpl  # noqa: E402
from python.auth_service.src.auth_service.infra.otp_store import RedisAuthOtpStore  # noqa: E402
from python.auth_service.src.auth_service.infra.password import PasswordServiceImpl  # noqa: E402
from python.auth_service.src.auth_service.repo.account import AccountRepoImpl  # noqa: E402
from python.auth_service.src.auth_service.usecase.auth_flow import AuthUseCaseImpl  # noqa: E402
from python.libs.clients.db import Database  # noqa: E402
from python.libs.entities.user import Gender  # noqa: E402
from python.libs.infra.redis_client import RedisClientImpl  # noqa: E402
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException  # noqa: E402

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
]


def _docker_available() -> bool:
    try:
        import docker

        docker.from_env().ping()
        return True
    except Exception:
        return False


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
        try:
            redis.stop()
        except Exception:
            pass
        try:
            pg.stop()
        except Exception:
            pass


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def auth_uc(containers):
    migrations_dir = PYTHON_ROOT / "auth_service" / "sql" / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))

    import psycopg2

    sync_url = containers["pg_sync_url"].replace("postgresql+psycopg2://", "postgresql://")
    conn = psycopg2.connect(sync_url)
    conn.autocommit = True
    cur = conn.cursor()
    for sql_file in sql_files:
        cur.execute(sql_file.read_text(encoding="utf-8"))
    cur.close()
    conn.close()

    db = object.__new__(Database)
    db.url = containers["pg_url"]
    db.echo = False
    db.pool_size = 3
    db.init()

    from sqlalchemy import text

    async with db.engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

    redis = object.__new__(RedisClientImpl)
    redis._client = None
    redis._url = f"redis://{containers['redis_host']}:{containers['redis_port']}/0"

    account_repo = object.__new__(AccountRepoImpl)
    account_repo.db = db

    otp_store = object.__new__(RedisAuthOtpStore)
    otp_store.redis_client = redis
    otp_store.otp_ttl_sec = 300

    jwt_svc = object.__new__(JwtServiceImpl)
    jwt_svc.init(jwt_secret="integration-test-secret", access_ttl_min=15, refresh_ttl_days=30)

    cfg = MagicMock()
    cfg.get_config.return_value = MagicMock(settings={"auth": {"google_client_ids": []}})

    pwd = object.__new__(PasswordServiceImpl)

    uc = object.__new__(AuthUseCaseImpl)
    uc.account_repo = account_repo
    uc.password_service = pwd
    uc.jwt_service = jwt_svc
    uc.otp_store = otp_store
    uc.outbox = AsyncMock()
    uc.user_client = MagicMock()
    _uid = {"n": 1000}

    def _create_user(*_a, **_k):
        _uid["n"] += 1
        return {"id": _uid["n"]}

    uc.user_client.create_user.side_effect = _create_user
    uc.user_client.delete_user = MagicMock()
    uc.config_service = cfg
    uc.otp_ttl_sec = 300
    uc.init(otp_ttl_sec=300)

    try:
        yield uc
    finally:
        await redis.close()
        await db.engine.dispose()


async def _register_active(uc: AuthUseCaseImpl, email: str, password: str = "SecurePass1!"):
    challenge = await uc.register(
        RegisterRequest(
            name="Integration User",
            identifier=email,
            password=password,
            birthdate=None,
            city_id=1,
            accept_terms=True,
            gender=Gender.MALE,
        )
    )
    stored = await uc.otp_store.get(challenge.challenge_id)
    assert stored is not None
    tokens = await uc.register_verify(
        VerifyOtpRequest(challenge_id=challenge.challenge_id, code=stored.code)
    )
    return challenge, tokens


async def test_register_otp_verify_integration(auth_uc):
    challenge = await auth_uc.register(
        RegisterRequest(
            name="Integration User",
            identifier="integration@example.com",
            password="SecurePass1!",
            birthdate=None,
            city_id=1,
            accept_terms=True,
            gender=Gender.MALE,
        )
    )
    assert challenge.challenge_id
    stored = await auth_uc.otp_store.get(challenge.challenge_id)
    assert stored is not None
    assert len(stored.code) == 6

    tokens = await auth_uc.register_verify(
        VerifyOtpRequest(challenge_id=challenge.challenge_id, code=stored.code)
    )
    assert tokens.access_token
    assert tokens.user_id == 1001
    auth_uc.user_client.create_user.assert_called()


async def test_login_refresh_logout_integration(auth_uc):
    email = "login.refresh@example.com"
    password = "SecurePass1!"
    _, reg_tokens = await _register_active(auth_uc, email, password)

    login_ch = await auth_uc.login(LoginRequest(identifier=email, password=password))
    stored = await auth_uc.otp_store.get(login_ch.challenge_id)
    assert stored is not None
    login_tokens = await auth_uc.login_verify(
        VerifyOtpRequest(challenge_id=login_ch.challenge_id, code=stored.code)
    )
    assert login_tokens.access_token
    assert login_tokens.user_id == reg_tokens.user_id

    refreshed = await auth_uc.refresh(RefreshTokenRequest(refresh_token=login_tokens.refresh_token))
    assert refreshed.refresh_token != login_tokens.refresh_token

    with pytest.raises(CoreException):
        await auth_uc.refresh(RefreshTokenRequest(refresh_token=login_tokens.refresh_token))

    ok = await auth_uc.logout(RefreshTokenRequest(refresh_token=refreshed.refresh_token))
    assert ok["ok"] is True

    with pytest.raises(CoreException):
        await auth_uc.refresh(RefreshTokenRequest(refresh_token=refreshed.refresh_token))


async def test_forgot_password_integration(auth_uc):
    email = "forgot@example.com"
    await _register_active(auth_uc, email, "OldPass1!")

    fake = await auth_uc.forgot_password(ForgotPasswordRequest(identifier="nobody@example.com"))
    assert fake.challenge_id
    assert await auth_uc.otp_store.get(fake.challenge_id) is None

    ch = await auth_uc.forgot_password(ForgotPasswordRequest(identifier=email))
    stored = await auth_uc.otp_store.get(ch.challenge_id)
    assert stored is not None and stored.purpose == "reset"
    reset = await auth_uc.forgot_verify(
        VerifyOtpRequest(challenge_id=ch.challenge_id, code=stored.code)
    )
    assert reset["reset_token"]

    new_password = "NewPass2!"
    ok = await auth_uc.reset_password(
        ResetPasswordRequest(reset_token=reset["reset_token"], new_password=new_password)
    )
    assert ok["ok"] is True

    with pytest.raises(CoreException):
        await auth_uc.login(LoginRequest(identifier=email, password="OldPass1!"))

    login_ch = await auth_uc.login(LoginRequest(identifier=email, password=new_password))
    assert login_ch.challenge_id


async def test_resend_otp_integration(auth_uc):
    email = "resend@example.com"
    await _register_active(auth_uc, email)
    login_ch = await auth_uc.login(LoginRequest(identifier=email, password="SecurePass1!"))
    old_id = login_ch.challenge_id
    resent = await auth_uc.resend_otp(old_id)
    assert resent.challenge_id != old_id
    stored = await auth_uc.otp_store.get(resent.challenge_id)
    assert stored is not None
    tokens = await auth_uc.login_verify(
        VerifyOtpRequest(challenge_id=resent.challenge_id, code=stored.code)
    )
    assert tokens.access_token
