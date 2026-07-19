"""
Transactional Outbox.

ENV: CITYVIBE_OUTBOX_ENABLED=true → пишем в таблицу outbox_messages, релей публикует в EventBus.
     false → Outbox.publish сразу зовёт EventBus (local-friendly).

Использование в use-case:
    await self.outbox.publish("user.created", UserCreatedEvent(user=user))
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Protocol

from sqlalchemy import Boolean, DateTime, Integer, String, Text, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.libs.clients.infra.events import EventBus
from python.libs.clients.infra.events.eventbus import serialize_message
from python.libs.infra.context import get_request_id
from python.libs.infra.flags import flags

logger = logging.getLogger(__name__)


class OutboxBase(DeclarativeBase):
    """Отдельный Base — сервисы применяют SQL-миграцию outbox самостоятельно."""


class OutboxMessageModel(OutboxBase):
    __tablename__ = "outbox_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Outbox(Protocol):
    """Контракт outbox: всегда publish(topic, message)."""

    async def publish(self, topic: str, message: Any) -> None:
        ...


@bean
class OutboxImpl(Outbox):
    """
    Если outbox выключен — прокси на EventBus.
    Если включён — INSERT в outbox_messages (релей заберёт).
    """

    db: Database
    event_bus: EventBus
    _relay_task: asyncio.Task | None = None

    def init(self, **kwargs):
        self._relay_task = None

    async def publish(self, topic: str, message: Any) -> None:
        if not flags().outbox:
            await self.event_bus.publish(topic, message)
            return

        body = serialize_message(message).decode("utf-8")
        row = OutboxMessageModel(
            topic=topic,
            payload=body,
            event_type=type(message).__name__,
            request_id=get_request_id(),
            published=False,
        )
        async with self.db.session() as session:
            session.add(row)

    async def flush_once(self, limit: int = 50) -> int:
        """Публикует пачку unpublished сообщений. Возвращает число опубликованных."""
        if not flags().outbox:
            return 0

        async with self.db.session() as session:
            stmt = (
                select(OutboxMessageModel)
                .where(OutboxMessageModel.published.is_(False))
                .order_by(OutboxMessageModel.id)
                .limit(limit)
            )
            rows = list((await session.execute(stmt)).scalars().all())
            for row in rows:
                # payload уже JSON-строка — EventBus.serialize умеет str → bytes
                await self.event_bus.publish(row.topic, row.payload)
                row.published = True
                row.published_at = datetime.now(timezone.utc)
            return len(rows)

    def start_relay(self) -> None:
        """Фоновый цикл (вызывать из Application.run при включённом флаге)."""
        if not flags().outbox:
            return
        if self._relay_task and not self._relay_task.done():
            return

        async def _loop():
            while True:
                try:
                    n = await self.flush_once()
                    if n:
                        logger.info("Outbox: опубликовано %s сообщений", n)
                except Exception:
                    logger.exception("Outbox relay error")
                await asyncio.sleep(flags().outbox_poll_sec)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._relay_task = loop.create_task(_loop())
            else:
                # uvicorn ещё не стартовал — стартуем через ensure позже
                self._relay_task = None
                self._pending_relay = True
        except RuntimeError:
            self._pending_relay = True
