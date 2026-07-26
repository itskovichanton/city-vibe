"""HTTP-сервер auth-service."""

from datetime import date
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_ioc_itskovichanton.utils import default_dataclass_field
from src.mybootstrap_mvc_fastapi_itskovichanton.error_handler import ErrorHandlerFastAPISupport
from src.mybootstrap_mvc_fastapi_itskovichanton.presenters import JSONResultPresenterImpl
from src.mybootstrap_mvc_itskovichanton.pipeline import ActionRunner, Result
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter

from python.libs.infra import CityVibeInfraSupport
from python.libs.infra.decorators import rate_limit
from python.libs.entities.user import Gender
from python.auth_service.src.auth_service.entities.common import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyOtpRequest,
)
from python.auth_service.src.auth_service.usecase.auth_flow import AuthUseCase


class RegisterBody(BaseModel):
    name: str
    identifier: str
    password: str
    birthdate: Optional[date] = None
    city_id: int
    accept_terms: bool = Field(..., description="Принятие условий")
    gender: Gender = Field(..., description="Пол")


class VerifyBody(BaseModel):
    challenge_id: str
    code: str = Field(..., min_length=6, max_length=6)


class LoginBody(BaseModel):
    identifier: str
    password: str


class ResendBody(BaseModel):
    challenge_id: str


class ForgotBody(BaseModel):
    identifier: str
    channel: Optional[str] = Field(None, description="email или phone")


class ResetBody(BaseModel):
    reset_token: str
    new_password: str


class RefreshBody(BaseModel):
    refresh_token: str


class GoogleBody(BaseModel):
    id_token: str
    city_id: Optional[int] = None
    name: Optional[str] = None
    birthdate: Optional[date] = None
    gender: Gender = Field(Gender.MALE, description="Пол")


@bean(port=("server.port", int, 8082), host=("server.host", str, "0.0.0.0"))
class Server:
    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    infra_support: CityVibeInfraSupport
    action_runner: ActionRunner
    auth_uc: AuthUseCase
    presenter: ResultPresenter = default_dataclass_field(JSONResultPresenterImpl(exclude_unset=True))

    def init(self, **kwargs):
        self.port = kwargs.get("port", getattr(self, "port", 8082))
        self.host = kwargs.get("host", getattr(self, "host", "0.0.0.0"))
        self.fast_api = self.init_fast_api()
        self.add_routes()

    def start(self):
        uvicorn.run(self.fast_api, port=self.port, host=self.host)

    def init_fast_api(self) -> FastAPI:
        app = FastAPI(
            title="City Vibe — Auth Service",
            description="Регистрация, логин, OTP, JWT",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )
        self.error_handler_fast_api_support.mount(app)
        self.infra_support.mount(app)
        return app

    def add_routes(self):
        @self.fast_api.get("/health", tags=["infra"])
        async def health():
            return self.presenter.present(Result(result={"status": "ok", "service": "auth-service"}))

        @self.fast_api.post("/auth/register", tags=["auth"])
        @rate_limit("auth.register", limit=20)
        async def register(request: Request, body: RegisterBody):
            req = RegisterRequest(
                name=body.name,
                identifier=body.identifier,
                password=body.password,
                birthdate=body.birthdate,
                city_id=body.city_id,
                accept_terms=body.accept_terms,
                gender=body.gender,
            )
            return self.presenter.present(await self.action_runner.run(self.auth_uc.register, call=req))

        @self.fast_api.post("/auth/register/verify", tags=["auth"])
        @rate_limit("auth.register.verify", limit=30)
        async def register_verify(request: Request, body: VerifyBody):
            req = VerifyOtpRequest(challenge_id=body.challenge_id, code=body.code)
            return self.presenter.present(await self.action_runner.run(self.auth_uc.register_verify, call=req))

        @self.fast_api.post("/auth/login", tags=["auth"])
        @rate_limit("auth.login", limit=30)
        async def login(request: Request, body: LoginBody):
            req = LoginRequest(identifier=body.identifier, password=body.password)
            return self.presenter.present(await self.action_runner.run(self.auth_uc.login, call=req))

        @self.fast_api.post("/auth/login/verify", tags=["auth"])
        @rate_limit("auth.login.verify", limit=30)
        async def login_verify(request: Request, body: VerifyBody):
            req = VerifyOtpRequest(challenge_id=body.challenge_id, code=body.code)
            return self.presenter.present(await self.action_runner.run(self.auth_uc.login_verify, call=req))

        @self.fast_api.post("/auth/otp/resend", tags=["auth"])
        @rate_limit("auth.otp.resend", limit=10)
        async def resend_otp(request: Request, body: ResendBody):
            return self.presenter.present(
                await self.action_runner.run(self.auth_uc.resend_otp, call=body.challenge_id)
            )

        @self.fast_api.post("/auth/password/forgot", tags=["auth"])
        @rate_limit("auth.password.forgot", limit=10)
        async def forgot_password(request: Request, body: ForgotBody):
            req = ForgotPasswordRequest(identifier=body.identifier, channel=body.channel)
            return self.presenter.present(await self.action_runner.run(self.auth_uc.forgot_password, call=req))

        @self.fast_api.post("/auth/password/forgot/verify", tags=["auth"])
        async def forgot_verify(request: Request, body: VerifyBody):
            req = VerifyOtpRequest(challenge_id=body.challenge_id, code=body.code)
            return self.presenter.present(await self.action_runner.run(self.auth_uc.forgot_verify, call=req))

        @self.fast_api.post("/auth/password/reset", tags=["auth"])
        async def reset_password(request: Request, body: ResetBody):
            req = ResetPasswordRequest(reset_token=body.reset_token, new_password=body.new_password)
            return self.presenter.present(await self.action_runner.run(self.auth_uc.reset_password, call=req))

        @self.fast_api.post("/auth/token/refresh", tags=["auth"])
        async def refresh_token(request: Request, body: RefreshBody):
            req = RefreshTokenRequest(refresh_token=body.refresh_token)
            return self.presenter.present(await self.action_runner.run(self.auth_uc.refresh, call=req))

        @self.fast_api.post("/auth/logout", tags=["auth"])
        async def logout(request: Request, body: RefreshBody):
            req = RefreshTokenRequest(refresh_token=body.refresh_token)
            return self.presenter.present(await self.action_runner.run(self.auth_uc.logout, call=req))

        @self.fast_api.post("/auth/social/google", tags=["auth"])
        @rate_limit("auth.social.google", limit=20)
        async def google_auth(request: Request, body: GoogleBody):
            req = GoogleAuthRequest(
                id_token=body.id_token,
                city_id=body.city_id,
                name=body.name,
                birthdate=body.birthdate,
                gender=body.gender,
            )
            return self.presenter.present(await self.action_runner.run(self.auth_uc.google, call=req))
