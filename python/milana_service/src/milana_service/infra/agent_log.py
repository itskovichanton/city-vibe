"""Запись в milana-agent JSON-лог.

LoggerService.SimpleJsonFormatter выкидывает поле `msg`. Поэтому
`logger.info(json.dumps(...))` оставляет в файле пустые строки `{t, taskName}`.
Словарь (как HTTP-middleware) попадает в JSON как поля записи.
"""

from __future__ import annotations

from logging import Logger
from typing import Any


def log_agent(logger: Logger, event: str, **payload: Any) -> None:
    try:
        logger.info({"event": event, **payload})
    except Exception:
        logger.info({"event": event, "log_error": "serialize_failed"})
