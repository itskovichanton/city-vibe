"""Контекст запроса (contextvars): request_id и пр. для логов / EventBus / outbox."""

from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4

_request_id: ContextVar[str | None] = ContextVar("cityvibe_request_id", default=None)
_service_name: ContextVar[str | None] = ContextVar("cityvibe_service_name", default=None)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(value: str | None) -> None:
    _request_id.set(value)


def ensure_request_id() -> str:
    rid = _request_id.get()
    if not rid:
        rid = str(uuid4())
        _request_id.set(rid)
    return rid


def get_service_name() -> str | None:
    return _service_name.get()


def set_service_name(value: str | None) -> None:
    _service_name.set(value)
