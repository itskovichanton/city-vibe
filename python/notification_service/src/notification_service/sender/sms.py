"""SMS-отправитель через mock-notify gateway (on_mbclient_api)."""

from __future__ import annotations

import logging
from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.domain.mock_notify.client import MockNotifyClient

logger = logging.getLogger(__name__)


class SmsSender(Protocol):
    async def send_otp(self, to: str, code: str, purpose: str) -> None: ...


@bean
class SmsSenderImpl(SmsSender):
    """Делегирует в MockNotifyClient (clients.mock_notify в config.yml)."""

    mock_notify_client: MockNotifyClient

    async def send_otp(self, to: str, code: str, purpose: str) -> None:
        text = f"CityVibe: код {code} ({purpose})"
        # on_mbclient_api — sync; в async-воркере вызываем напрямую (короткий HTTP)
        self.mock_notify_client.send_sms(to=to, text=text)
        logger.info("SMS отправлен → %s", to)
