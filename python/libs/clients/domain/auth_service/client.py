"""HTTP-клиент auth-service (on_mbclient_api + requests)."""

from __future__ import annotations

from typing import Any, Protocol

from src.mybootstrap_core_itskovichanton.utils import to_dict
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_fastapi_itskovichanton.client.http import on_mbclient_api

from python.libs.clients.domain.auth_service.entities import (
    ForgotBody,
    GoogleBody,
    LoginBody,
    RefreshBody,
    RegisterBody,
    ResendBody,
    ResetBody,
    VerifyBody,
)

api_call = on_mbclient_api(_name="clients.auth_service")


class AuthServiceClient(Protocol):
    def health(self) -> Any: ...

    def register(self, body: RegisterBody) -> Any: ...

    def register_verify(self, body: VerifyBody) -> Any: ...

    def login(self, body: LoginBody) -> Any: ...

    def login_verify(self, body: VerifyBody) -> Any: ...

    def resend_otp(self, body: ResendBody) -> Any: ...

    def forgot_password(self, body: ForgotBody) -> Any: ...

    def forgot_verify(self, body: VerifyBody) -> Any: ...

    def reset_password(self, body: ResetBody) -> Any: ...

    def refresh(self, body: RefreshBody) -> Any: ...

    def logout(self, body: RefreshBody) -> Any: ...

    def google(self, body: GoogleBody) -> Any: ...


@bean
class AuthServiceClientImpl(AuthServiceClient):
    @api_call
    def health(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/health", timeout=30, headers=headers)

    @api_call
    def register(self, body: RegisterBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/register",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def register_verify(self, body: VerifyBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/register/verify",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def login(self, body: LoginBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/login",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def login_verify(self, body: VerifyBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/login/verify",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def resend_otp(self, body: ResendBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/otp/resend",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def forgot_password(self, body: ForgotBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/password/forgot",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def forgot_verify(self, body: VerifyBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/password/forgot/verify",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def reset_password(self, body: ResetBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/password/reset",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def refresh(self, body: RefreshBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/token/refresh",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def logout(self, body: RefreshBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/logout",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def google(self, body: GoogleBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/auth/social/google",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )
