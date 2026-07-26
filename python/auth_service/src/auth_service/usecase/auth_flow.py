"""Use-cases auth-service: регистрация, логин, OTP, JWT, Google."""

from __future__ import annotations

import secrets
import uuid
from datetime import date, datetime, timezone
from typing import Optional, Protocol

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.libs.entities.events import (
    AuthOtpRequestedEvent,
    AuthUserRegisteredEvent,
    TOPIC_AUTH_OTP_REQUESTED,
    TOPIC_AUTH_USER_REGISTERED,
)
from python.libs.infra.identifier import IdentifierType, mask_identifier, parse_identifier
from python.libs.infra.outbox import Outbox
from python.libs.infra.saga import SagaContext, saga, saga_step
from python.auth_service.src.auth_service.entities.common import (
    AuthTokensResponse,
    ChallengeResponse,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyOtpRequest,
)
from python.libs.clients.domain.user_service.client import UserServiceClient
from python.libs.clients.domain.user_service.entities import CreateUserBody
from python.auth_service.src.auth_service.infra.jwt_service import JwtService
from python.auth_service.src.auth_service.infra.otp_common import AuthOtpStore, OtpChallenge, generate_otp_code
from python.auth_service.src.auth_service.infra.password import PasswordService
from python.auth_service.src.auth_service.repo.account import AccountRepo


def _user_id_from_result(result) -> int:
    if isinstance(result, dict):
        return int(result["id"])
    return int(result.id)


async def _compensate_user_created(user_id: int, self, _account, **_kwargs) -> None:
    """Компенсация saga: soft-delete пользователя при откате."""
    self.user_client.delete_user(user_id)


class AuthUseCase(Protocol):
    async def register(self, req: RegisterRequest) -> ChallengeResponse: ...
    async def register_verify(self, req: VerifyOtpRequest, saga_ctx: SagaContext | None = None) -> AuthTokensResponse: ...
    async def login(self, req: LoginRequest) -> ChallengeResponse: ...
    async def login_verify(self, req: VerifyOtpRequest) -> AuthTokensResponse: ...
    async def resend_otp(self, challenge_id: str) -> ChallengeResponse: ...
    async def forgot_password(self, req: ForgotPasswordRequest) -> ChallengeResponse: ...
    async def forgot_verify(self, req: VerifyOtpRequest) -> dict: ...
    async def reset_password(self, req: ResetPasswordRequest) -> dict: ...
    async def refresh(self, req: RefreshTokenRequest) -> AuthTokensResponse: ...
    async def logout(self, req: RefreshTokenRequest) -> dict: ...
    async def google(self, req: GoogleAuthRequest) -> AuthTokensResponse: ...


@bean(otp_ttl_sec=("auth.otp_ttl_sec", int, 300))
class AuthUseCaseImpl(AuthUseCase):
    account_repo: AccountRepo
    password_service: PasswordService
    jwt_service: JwtService
    otp_store: AuthOtpStore
    outbox: Outbox
    user_client: UserServiceClient
    config_service: ConfigService
    otp_ttl_sec: int = 300

    def init(self, **kwargs):
        self._otp_ttl = int(kwargs.get("otp_ttl_sec", getattr(self, "otp_ttl_sec", 300)))
        settings = self.config_service.get_config().settings
        auth_cfg = settings.get("auth", {}) if settings else {}
        self._google_client_ids = auth_cfg.get("google_client_ids", []) if auth_cfg else []

    def _channel(self, id_type: IdentifierType) -> str:
        return "email" if id_type == IdentifierType.EMAIL else "sms"

    async def _issue_tokens(self, account_id: int) -> AuthTokensResponse:
        account = await self.account_repo.get_by_id(account_id)
        user_id = account.user_id if account else None
        access, expires_in = self.jwt_service.create_access_token(account_id, user_id=user_id)
        refresh_raw, refresh_hash, expires_at = self.jwt_service.create_refresh_token()
        await self.account_repo.save_refresh_token(account_id, refresh_hash, expires_at)
        return AuthTokensResponse(
            access_token=access,
            refresh_token=refresh_raw,
            expires_in=expires_in,
            user_id=user_id,
            account_id=account_id,
        )

    async def _create_challenge(
        self,
        *,
        purpose: str,
        parsed,
        account_id: int | None = None,
        extra: dict | None = None,
    ) -> ChallengeResponse:
        challenge_id = str(uuid.uuid4())
        code = generate_otp_code()
        channel = self._channel(parsed.type)
        challenge = OtpChallenge(
            challenge_id=challenge_id,
            code=code,
            purpose=purpose,
            channel=channel,
            destination=parsed.value,
            account_id=account_id,
            extra=extra,
        )
        await self.otp_store.save(challenge, self._otp_ttl)
        await self.outbox.publish(
            TOPIC_AUTH_OTP_REQUESTED,
            AuthOtpRequestedEvent(
                challenge_id=challenge_id,
                purpose=purpose,
                channel=channel,
                destination=parsed.value,
                code=code,
            ),
        )
        return ChallengeResponse(
            challenge_id=challenge_id,
            channel=channel,
            destination_masked=mask_identifier(parsed),
            expires_in=self._otp_ttl,
        )

    async def register(self, req: RegisterRequest) -> ChallengeResponse:
        if not req.accept_terms:
            raise CoreException(message="Необходимо принять условия использования")
        parsed = parse_identifier(req.identifier)
        existing = await self.account_repo.find_by_identity(parsed.type.value, parsed.value)
        if existing is not None:
            raise CoreException(message="Аккаунт с таким email или телефоном уже существует")
        pwd_hash = self.password_service.hash(req.password)
        account = await self.account_repo.create_pending(
            name=req.name,
            password_hash=pwd_hash,
            identity_type=parsed.type.value,
            identity_value=parsed.value,
            birthdate=req.birthdate,
            city_id=req.city_id,
            accept_terms=req.accept_terms,
        )
        return await self._create_challenge(
            purpose="register",
            parsed=parsed,
            account_id=account.id,
        )

    @saga("register.verify")
    async def register_verify(
        self, req: VerifyOtpRequest, saga_ctx: SagaContext | None = None
    ) -> AuthTokensResponse:
        challenge = await self._verify_challenge(req, purpose="register")
        account = await self.account_repo.get_by_id(challenge.account_id or 0)
        if account is None:
            raise CoreException(message="Аккаунт не найден")
        user_id = await self._create_user_with_compensation(account, saga_ctx=saga_ctx)
        await self.account_repo.activate(account.id, user_id)
        email = challenge.destination if challenge.channel == "email" else None
        phone = challenge.destination if challenge.channel == "sms" else None
        await self.outbox.publish(
            TOPIC_AUTH_USER_REGISTERED,
            AuthUserRegisteredEvent(
                user_id=user_id,
                account_id=account.id,
                email=email,
                phone=phone,
                name=account.name,
            ),
        )
        await self.otp_store.delete(req.challenge_id)
        return await self._issue_tokens(account.id)

    @saga_step(compensate=_compensate_user_created)
    async def _create_user_with_compensation(self, account, saga_ctx: SagaContext | None):
        result = self.user_client.create_user(
            CreateUserBody(
                name=account.name,
                auth_account_id=account.id,
                city_id=account.city_id,
                birthdate=account.birthdate.isoformat() if account.birthdate else None,
            )
        )
        return _user_id_from_result(result)

    async def _verify_challenge(self, req: VerifyOtpRequest, purpose: str) -> OtpChallenge:
        challenge = await self.otp_store.get(req.challenge_id)
        if challenge is None:
            raise CoreException(message="Challenge не найден или истёк")
        if challenge.purpose != purpose:
            raise CoreException(message="Неверный тип challenge")
        if challenge.code != req.code.strip():
            raise CoreException(message="Неверный код")
        return challenge

    async def login(self, req: LoginRequest) -> ChallengeResponse:
        parsed = parse_identifier(req.identifier)
        account = await self.account_repo.find_by_identity(parsed.type.value, parsed.value)
        if account is None or account.status != "active":
            raise CoreException(message="Неверный логин или пароль")
        if not self.password_service.verify(req.password, account.password_hash):
            raise CoreException(message="Неверный логин или пароль")
        return await self._create_challenge(purpose="login", parsed=parsed, account_id=account.id)

    async def login_verify(self, req: VerifyOtpRequest) -> AuthTokensResponse:
        challenge = await self._verify_challenge(req, purpose="login")
        await self.otp_store.delete(req.challenge_id)
        return await self._issue_tokens(challenge.account_id or 0)

    async def resend_otp(self, challenge_id: str) -> ChallengeResponse:
        old = await self.otp_store.get(challenge_id)
        if old is None:
            raise CoreException(message="Challenge не найден")
        parsed = parse_identifier(old.destination)
        return await self._create_challenge(
            purpose=old.purpose,
            parsed=parsed,
            account_id=old.account_id,
            extra=old.extra,
        )

    async def forgot_password(self, req: ForgotPasswordRequest) -> ChallengeResponse:
        parsed = parse_identifier(req.identifier)
        account = await self.account_repo.find_by_identity(parsed.type.value, parsed.value)
        if account is None:
            # Не раскрываем наличие аккаунта
            return ChallengeResponse(
                challenge_id=str(uuid.uuid4()),
                channel=self._channel(parsed.type),
                destination_masked=mask_identifier(parsed),
                expires_in=self._otp_ttl,
            )
        return await self._create_challenge(purpose="reset", parsed=parsed, account_id=account.id)

    async def forgot_verify(self, req: VerifyOtpRequest) -> dict:
        challenge = await self._verify_challenge(req, purpose="reset")
        reset_token = secrets.token_urlsafe(32)
        reset_challenge = OtpChallenge(
            challenge_id=reset_token,
            code="",
            purpose="reset_confirm",
            channel=challenge.channel,
            destination=challenge.destination,
            account_id=challenge.account_id,
            extra={"verified": True},
        )
        await self.otp_store.save(reset_challenge, self._otp_ttl)
        await self.otp_store.delete(req.challenge_id)
        return {"reset_token": reset_token, "expires_in": self._otp_ttl}

    async def reset_password(self, req: ResetPasswordRequest) -> dict:
        challenge = await self.otp_store.get(req.reset_token)
        if challenge is None or challenge.purpose != "reset_confirm":
            raise CoreException(message="Reset token недействителен")
        account = await self.account_repo.get_by_id(challenge.account_id or 0)
        if account is None:
            raise CoreException(message="Аккаунт не найден")
        pwd_hash = self.password_service.hash(req.new_password)
        await self.account_repo.update_password(account.id, pwd_hash)
        await self.otp_store.delete(req.reset_token)
        return {"ok": True}

    async def refresh(self, req: RefreshTokenRequest) -> AuthTokensResponse:
        token_hash = self.jwt_service.hash_refresh_token(req.refresh_token)
        row = await self.account_repo.find_refresh_token(token_hash)
        if row is None or row.expires_at < datetime.now(timezone.utc):
            raise CoreException(message="Refresh token недействителен")
        await self.account_repo.revoke_refresh_token(token_hash)
        return await self._issue_tokens(row.account_id)

    async def logout(self, req: RefreshTokenRequest) -> dict:
        token_hash = self.jwt_service.hash_refresh_token(req.refresh_token)
        await self.account_repo.revoke_refresh_token(token_hash)
        return {"ok": True}

    async def google(self, req: GoogleAuthRequest) -> AuthTokensResponse:
        if not self._google_client_ids:
            raise CoreException(message="Google OAuth не настроен (auth.google_client_ids)")
        request = google_requests.Request()
        info = None
        last_err: Exception | None = None
        for client_id in self._google_client_ids:
            try:
                info = google_id_token.verify_oauth2_token(req.id_token, request, audience=client_id)
                break
            except Exception as e:
                last_err = e
                continue
        if info is None:
            raise CoreException(message=f"Неверный Google token: {last_err}")
        sub = info["sub"]
        email = info.get("email")
        account = await self.account_repo.find_oauth("google", sub)
        if account is None:
            name = req.name or info.get("name", "User")
            account = await self.account_repo.create_pending(
                name=name,
                password_hash="",
                identity_type="email" if email else "phone",
                identity_value=email or f"google:{sub}",
                birthdate=req.birthdate,
                city_id=req.city_id,
                accept_terms=True,
            )
            await self.account_repo.link_oauth(account.id, "google", sub, email)
            user_id = _user_id_from_result(
                self.user_client.create_user(
                    CreateUserBody(
                        name=name,
                        auth_account_id=account.id,
                        city_id=req.city_id,
                        birthdate=req.birthdate.isoformat() if req.birthdate else None,
                    )
                )
            )
            account = await self.account_repo.activate(account.id, user_id)
        return await self._issue_tokens(account.id)
