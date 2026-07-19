"""
Шина событий на базе RabbitMQ.

Bean `RabbitMQEventBus` реализует протокол `EventBus`:
- publish — отправка любого объекта в топик (routing key);
- subscribe — подписка на топик по имени, асинхронный поток сообщений.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, AsyncIterator, Protocol
from uuid import UUID

import aio_pika
from aio_pika import ExchangeType, IncomingMessage
from aio_pika.abc import AbstractChannel, AbstractExchange, AbstractRobustConnection
from src.mybootstrap_ioc_itskovichanton.ioc import bean

logger = logging.getLogger(__name__)

# Имя topic-exchange по умолчанию для всех сервисов City Vibe
DEFAULT_EXCHANGE = "city_vibe.events"


class EventBus(Protocol):
    """Контракт шины событий (publish / subscribe)."""

    async def publish(self, topic: str, message: Any) -> None:
        """Отправка любого объекта в топик (Exchange + routing_key)."""
        ...

    def subscribe(self, topic: str, queue_name: str) -> AsyncIterator[Any]:
        """
        Подписка на топик по имени.

        Возвращает асинхронный итератор сообщений (уже десериализованных).
        Метод НЕ async — он только создаёт и возвращает async-генератор.
        """
        ...


def _json_default(obj: Any) -> Any:
    """Сериализация типов, которые json не умеет из коробки."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    raise TypeError(f"Объект типа {type(obj)!r} нельзя сериализовать в JSON")


def serialize_message(message: Any) -> bytes:
    """Упаковка произвольного объекта в UTF-8 JSON."""
    if isinstance(message, (bytes, bytearray)):
        return bytes(message)
    if isinstance(message, str):
        return message.encode("utf-8")
    payload = asdict(message) if is_dataclass(message) and not isinstance(message, type) else message
    return json.dumps(payload, default=_json_default, ensure_ascii=False).encode("utf-8")


def deserialize_message(body: bytes) -> Any:
    """Распаковка тела сообщения. Если не JSON — отдаём сырые bytes."""
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return body


@bean(
    url=("rabbitmq.url", str, "amqp://guest:guest@localhost:5672/"),
    exchange_name=("rabbitmq.exchange", str, DEFAULT_EXCHANGE),
)
class RabbitMQEventBus(EventBus):
    """
    Реализация EventBus поверх RabbitMQ (aio-pika).

    Топик = routing_key topic-exchange.
    Очередь привязывается к exchange с ключом = имя топика.

    Параметры url / exchange_name инжектятся фреймворком из config.yml
    через аргументы декоратора @bean(...).
    """

    # Ленивые поля соединения (заполняются при первом обращении)
    _connection: AbstractRobustConnection | None = None
    _channel: AbstractChannel | None = None
    _exchange: AbstractExchange | None = None
    _lock: asyncio.Lock | None = None

    def init(self, **kwargs):
        # Lock создаём здесь — event loop ещё может быть не запущен в __init__
        self._lock = asyncio.Lock()
        self._connection = None
        self._channel = None
        self._exchange = None
        # Значения из @bean kwargs уже выставлены setattr'ом; дублируем для ясности
        self.url = kwargs.get("url", getattr(self, "url", "amqp://guest:guest@localhost:5672/"))
        self.exchange_name = kwargs.get(
            "exchange_name",
            getattr(self, "exchange_name", DEFAULT_EXCHANGE),
        )

    async def _ensure_connected(self) -> AbstractExchange:
        """Гарантирует живое соединение, канал и topic-exchange."""
        if self._lock is None:
            self._lock = asyncio.Lock()

        async with self._lock:
            if self._exchange is not None and self._connection is not None and not self._connection.is_closed:
                return self._exchange

            logger.info("Подключение EventBus к RabbitMQ: %s", self.url)
            self._connection = await aio_pika.connect_robust(self.url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=50)

            # Topic-exchange: гибкая маршрутизация по имени топика
            self._exchange = await self._channel.declare_exchange(
                self.exchange_name,
                ExchangeType.TOPIC,
                durable=True,
            )
            return self._exchange

    async def publish(self, topic: str, message: Any) -> None:
        """Публикует любой объект в указанный топик."""
        if not topic:
            raise ValueError("topic не может быть пустым")

        exchange = await self._ensure_connected()
        body = serialize_message(message)

        await exchange.publish(
            aio_pika.Message(
                body=body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                type=type(message).__name__,
            ),
            routing_key=topic,
        )
        logger.debug("Опубликовано в топик %s (%d байт)", topic, len(body))

    def subscribe(self, topic: str, queue_name: str) -> AsyncIterator[Any]:
        """Возвращает async-генератор сообщений из топика."""
        if not topic:
            raise ValueError("topic не может быть пустым")
        if not queue_name:
            raise ValueError("queue_name не может быть пустым")

        return self._subscribe_generator(topic, queue_name)

    async def _subscribe_generator(self, topic: str, queue_name: str) -> AsyncIterator[Any]:
        """Внутренний генератор: объявляет очередь, биндит к топику, yield'ит сообщения."""
        await self._ensure_connected()
        assert self._channel is not None

        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.bind(self._exchange, routing_key=topic)
        logger.info("Подписка на топик '%s' через очередь '%s'", topic, queue_name)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                incoming: IncomingMessage = message
                async with incoming.process():
                    yield deserialize_message(incoming.body)

    async def close(self) -> None:
        """Корректное закрытие соединения (вызывать при остановке сервиса)."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("EventBus: соединение с RabbitMQ закрыто")
        self._connection = None
        self._channel = None
        self._exchange = None
