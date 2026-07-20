"""HTTP-клиент notification-service (health only)."""

from __future__ import annotations

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_fastapi_itskovichanton.client.http import on_mbclient_api

api_call = on_mbclient_api(_name="clients.notification_service")


class NotificationServiceClient(Protocol):
    def health(self) -> Any: ...


@bean
class NotificationServiceClientImpl(NotificationServiceClient):
    @api_call
    def health(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/health", timeout=30, headers=headers)
