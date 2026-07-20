"""HTTP-клиент mock-notify gateway (Result envelope)."""

from __future__ import annotations

from typing import Any, Protocol

from src.mybootstrap_core_itskovichanton.utils import to_dict
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_fastapi_itskovichanton.client.http import on_mbclient_api

from python.libs.clients.domain.mock_notify.entities import EmailIn, SmsIn

api_call = on_mbclient_api(_name="clients.mock_notify")


class MockNotifyClient(Protocol):
    def health(self) -> Any: ...

    def send_sms(self, to: str, text: str) -> Any: ...

    def send_email(self, to: str, subject: str, html: str = "", text: str = "") -> Any: ...


@bean
class MockNotifyClientImpl(MockNotifyClient):
    @api_call
    def health(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/health", timeout=30, headers=headers)

    @api_call
    def send_sms(self, to: str, text: str, session=None, url=None, headers=None):
        body = SmsIn(to=to, text=text)
        return session.post(
            url=f"{url}/sms",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def send_email(
        self,
        to: str,
        subject: str,
        html: str = "",
        text: str = "",
        session=None,
        url=None,
        headers=None,
    ):
        body = EmailIn(to=to, subject=subject, html=html, text=text)
        return session.post(
            url=f"{url}/email",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )
