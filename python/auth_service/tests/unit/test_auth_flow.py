"""Жёсткие unit-тесты auth-flow на InMemory OTP + fake repo."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.auth_service.src.auth_service.entities.common import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyOtpRequest,
)
from python.auth_service.src.auth_service.infra.jwt_service import JwtServiceImpl
from python.auth_service.src.auth_service.infra.otp_common import InMemoryAuthOtpStore, OtpChallenge
from python.auth_service.src.auth_service.infra.password import PasswordServiceImpl
from python.auth_service.src.auth_service.usecase.auth_flow import AuthUseCaseImpl
from python.libs.infra.saga import SagaContext


@dataclass
class FakeAccount:
    id: int
    name: str
    password_hash: str
    status: str = "pending"
    user_id: Optional[int] = None
    birthdate: Optional[date] = None
    city_id: Optional[int] = None
    accept_terms: bool = True


class FakeAccountRepo:
    def __init__(self):
        self.accounts: dict[int, FakeAccount] = {}
        self.identities: dict[tuple[str, str], int] = {}
        self.refresh: dict[str, Any] = {}
        self._seq = 0

    async def create_pending(self, **kwargs) -> FakeAccount:
        self._seq += 1
        acc = FakeAccount(
            id=self._seq,
            name=kwargs["name"],
            password_hash=kwargs["password_hash"],
            birthdate=kwargs.get("birthdate"),
            city_id=kwargs.get("city_id"),
            accept_terms=kwargs.get("accept_terms", True),
        )
        self.accounts[acc.id] = acc
        self.identities[(kwargs["identity_type"], kwargs["identity_value"])] = acc.id
        return acc

    async def find_by_identity(self, type_: str, value: str) -> Optional[FakeAccount]:
        aid = self.identities.get((type_, value))
        return self.accounts.get(aid) if aid else None

    async def get_by_id(self, account_id: int) -> Optional[FakeAccount]:
        return self.accounts.get(account_id)

    async def activate(self, account_id: int, user_id: int) -> FakeAccount:
        acc = self.accounts[account_id]
        acc.status = "active"
        acc.user_id = user_id
        return acc

    async def update_password(self, account_id: int, password_hash: str) -> None:
        self.accounts[account_id].password_hash = password_hash

    async def save_refresh_token(self, account_id: int, token_hash: str, expires_at) -> None:
        self.refresh[token_hash] = MagicMock(account_id=account_id, expires_at=expires_at)

    async def find_refresh_token(self, token_hash: str):
        return self.refresh.get(token_hash)

    async def revoke_refresh_token(self, token_hash: str) -> None:
        self.refresh.pop(token_hash, None)

    async def find_oauth(self, provider: str, sub: str):
        return None

    async def link_oauth(self, *args, **kwargs):
        return None


@pytest.fixture
def auth_uc():
    # Bypass @bean __init__ (requires IoC wiring)
    uc = object.__new__(AuthUseCaseImpl)
    uc.account_repo = FakeAccountRepo()
    uc.password_service = PasswordServiceImpl()
    cfg = MagicMock()
    cfg.get_config.return_value = MagicMock(settings={"auth": {"google_client_ids": []}})
    uc.config_service = cfg
    jwt_svc = object.__new__(JwtServiceImpl)
    jwt_svc.init(jwt_secret="test-secret", access_ttl_min=15, refresh_ttl_days=30)
    uc.jwt_service = jwt_svc
    uc.otp_store = InMemoryAuthOtpStore()
    uc.outbox = AsyncMock()
    uc.user_client = MagicMock()
    uc.user_client.create_user.return_value = {"id": 42}
    uc.user_client.delete_user = MagicMock()
    uc.init(otp_ttl_sec=300)
    return uc


@pytest.mark.asyncio
async def test_register_then_verify_issues_jwt_with_user_id(auth_uc):
    challenge = await auth_uc.register(
        RegisterRequest(
            name="Анна",
            identifier="anna@cityvibe.example",
            password="SecurePass1!",
            birthdate=date(1995, 5, 1),
            city_id=1,
            accept_terms=True,
        )
    )
    assert challenge.channel == "email"
    assert challenge.challenge_id

    # Достаём код из InMemory store
    stored = await auth_uc.otp_store.get(challenge.challenge_id)
    assert stored is not None
    assert len(stored.code) == 6

    tokens = await auth_uc.register_verify(
        VerifyOtpRequest(challenge_id=challenge.challenge_id, code=stored.code)
    )
    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.user_id == 42
    assert tokens.account_id == 1
    auth_uc.user_client.create_user.assert_called_once()
    auth_uc.outbox.publish.assert_awaited()


@pytest.mark.asyncio
async def test_login_wrong_password(auth_uc):
    await auth_uc.register(
        RegisterRequest(
            name="Bob",
            identifier="+79991234567",
            password="GoodPass99!",
            birthdate=None,
            city_id=1,
            accept_terms=True,
        )
    )
    # Активируем вручную
    acc = await auth_uc.account_repo.find_by_identity("phone", "+79991234567")
    await auth_uc.account_repo.activate(acc.id, 7)

    with pytest.raises(CoreException):
        await auth_uc.login(LoginRequest(identifier="+79991234567", password="wrong"))


@pytest.mark.asyncio
async def test_login_verify_flow(auth_uc):
    await auth_uc.register(
        RegisterRequest(
            name="Bob",
            identifier="bob@test.com",
            password="GoodPass99!",
            birthdate=None,
            city_id=1,
            accept_terms=True,
        )
    )
    acc = await auth_uc.account_repo.find_by_identity("email", "bob@test.com")
    await auth_uc.account_repo.activate(acc.id, 9)

    ch = await auth_uc.login(LoginRequest(identifier="bob@test.com", password="GoodPass99!"))
    stored = await auth_uc.otp_store.get(ch.challenge_id)
    tokens = await auth_uc.login_verify(VerifyOtpRequest(challenge_id=ch.challenge_id, code=stored.code))
    assert tokens.user_id == 9


@pytest.mark.asyncio
async def test_forgot_reset_password(auth_uc):
    await auth_uc.register(
        RegisterRequest(
            name="Cat",
            identifier="cat@test.com",
            password="OldPass11!",
            birthdate=None,
            city_id=1,
            accept_terms=True,
        )
    )
    acc = await auth_uc.account_repo.find_by_identity("email", "cat@test.com")
    await auth_uc.account_repo.activate(acc.id, 3)

    from python.auth_service.src.auth_service.entities.common import ForgotPasswordRequest

    ch = await auth_uc.forgot_password(ForgotPasswordRequest(identifier="cat@test.com"))
    stored = await auth_uc.otp_store.get(ch.challenge_id)
    reset = await auth_uc.forgot_verify(VerifyOtpRequest(challenge_id=ch.challenge_id, code=stored.code))
    assert "reset_token" in reset
    await auth_uc.reset_password(
        ResetPasswordRequest(reset_token=reset["reset_token"], new_password="NewPass22!")
    )
    # Логин со старым паролем — fail
    with pytest.raises(CoreException):
        await auth_uc.login(LoginRequest(identifier="cat@test.com", password="OldPass11!"))
    # С новым — OTP challenge
    ch2 = await auth_uc.login(LoginRequest(identifier="cat@test.com", password="NewPass22!"))
    assert ch2.challenge_id


@pytest.mark.asyncio
async def test_saga_compensates_when_token_issue_fails(auth_uc, monkeypatch):
    await auth_uc.register(
        RegisterRequest(
            name="Saga",
            identifier="saga@test.com",
            password="SagaPass1!",
            birthdate=None,
            city_id=1,
            accept_terms=True,
        )
    )
    ch = list(auth_uc.otp_store._store.values())[0][0]  # type: ignore[attr-defined]
    # Ломаем issue tokens после create_user
    async def boom(*_a, **_k):
        raise RuntimeError("jwt boom")

    monkeypatch.setattr(auth_uc, "_issue_tokens", boom)
    stored = await auth_uc.otp_store.get(ch.challenge_id)
    with pytest.raises(RuntimeError):
        await auth_uc.register_verify(
            VerifyOtpRequest(challenge_id=ch.challenge_id, code=stored.code)
        )
    auth_uc.user_client.delete_user.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_resend_otp(auth_uc):
    ch = await auth_uc.register(
        RegisterRequest(
            name="Resend",
            identifier="resend@test.com",
            password="Pass12345!",
            birthdate=None,
            city_id=1,
            accept_terms=True,
        )
    )
    ch2 = await auth_uc.resend_otp(ch.challenge_id)
    assert ch2.challenge_id
    assert ch2.channel == "email"


@pytest.mark.asyncio
async def test_refresh_and_logout(auth_uc):
    await auth_uc.register(
        RegisterRequest(
            name="Refresh",
            identifier="refresh@test.com",
            password="Pass12345!",
            birthdate=None,
            city_id=1,
            accept_terms=True,
        )
    )
    stored = list(auth_uc.otp_store._store.values())[0][0]  # type: ignore[attr-defined]
    tokens = await auth_uc.register_verify(
        VerifyOtpRequest(challenge_id=stored.challenge_id, code=stored.code)
    )
    refreshed = await auth_uc.refresh(RefreshTokenRequest(refresh_token=tokens.refresh_token))
    assert refreshed.access_token
    await auth_uc.logout(RefreshTokenRequest(refresh_token=refreshed.refresh_token))
