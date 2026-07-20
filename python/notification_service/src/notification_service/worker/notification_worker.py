"""Consumer событий RabbitMQ: OTP, welcome."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.infra.events import EventBus
from python.libs.entities.events import (
    TOPIC_AUTH_OTP_REQUESTED,
    TOPIC_AUTH_USER_REGISTERED,
)
from python.notification_service.src.notification_service.sender.email import EmailSender
from python.notification_service.src.notification_service.sender.sms import SmsSender

logger = logging.getLogger(__name__)

SUBSCRIPTIONS = [
    (TOPIC_AUTH_OTP_REQUESTED, "notification.auth.otp"),
    (TOPIC_AUTH_USER_REGISTERED, "notification.auth.registered"),
    ("user.created", "notification.user.created"),
]


@bean
class NotificationWorker:
    """Подписывается на топики при старте и обрабатывает события."""

    event_bus: EventBus
    email_sender: EmailSender
    sms_sender: SmsSender
    _tasks: list[asyncio.Task] | None = None

    def init(self, **kwargs):
        self._tasks = []

    async def start(self) -> None:
        for topic, queue in SUBSCRIPTIONS:
            task = asyncio.create_task(self._consume(topic, queue))
            self._tasks.append(task)
            logger.info("NotificationWorker: подписка %s → %s", topic, queue)

    async def _consume(self, topic: str, queue_name: str) -> None:
        async for message in self.event_bus.subscribe(topic, queue_name):
            try:
                await self._handle(topic, message)
            except Exception:
                logger.exception("Ошибка обработки %s", topic)

    async def _handle(self, topic: str, message: Any) -> None:
        if isinstance(message, dict):
            data = message
        else:
            data = message
        if topic == TOPIC_AUTH_OTP_REQUESTED:
            channel = data.get("channel", "email")
            if channel == "email":
                await self.email_sender.send_otp(
                    data["destination"],
                    data["code"],
                    data.get("purpose", "login"),
                )
            else:
                await self.sms_sender.send_otp(
                    data["destination"],
                    data["code"],
                    data.get("purpose", "login"),
                )
        elif topic == TOPIC_AUTH_USER_REGISTERED:
            email = data.get("email")
            if email:
                await self.email_sender.send_welcome(email, data.get("name", ""))
        elif topic == "user.created":
            logger.info("user.created: %s", data)
