"""Удобные реэкспорты декораторов для хендлеров микросервисов."""

from python.libs.infra.idempotency import idempotent
from python.libs.infra.rate_limit import rate_limit
from python.libs.infra.s2s import require_s2s
from python.libs.infra.upload import read_validated_upload, validate_upload

__all__ = [
    "idempotent",
    "rate_limit",
    "require_s2s",
    "validate_upload",
    "read_validated_upload",
]
