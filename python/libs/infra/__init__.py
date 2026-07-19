"""
Общая инфраструктура микросервисов City Vibe.

Библиотеки: asgi-correlation-id (request-id), pyrate-limiter (rate-limit),
filetype (upload MIME). Свои: S2S, idempotency, outbox.

Включение фич — через ENV (см. flags.py / .env.example).
Локально всё можно выключить и разрабатывать без Redis/S2S.
"""

from python.libs.infra.decorators import (
    idempotent,
    rate_limit,
    read_validated_upload,
    require_s2s,
    validate_upload,
)
from python.libs.infra.flags import InfraFlags, flags
from python.libs.infra.outbox import Outbox, OutboxImpl
from python.libs.infra.support import CityVibeInfraSupport

__all__ = [
    "InfraFlags",
    "flags",
    "CityVibeInfraSupport",
    "Outbox",
    "OutboxImpl",
    "idempotent",
    "rate_limit",
    "require_s2s",
    "validate_upload",
    "read_validated_upload",
]
