"""
Валидация upload (размер + MIME).

ENV: CITYVIBE_UPLOAD_VALIDATION_ENABLED=true (default on)
"""

from __future__ import annotations

import functools
from typing import Callable

from fastapi import UploadFile
from src.mybootstrap_mvc_itskovichanton.exceptions import ERR_REASON_VALIDATION, CoreException

from python.libs.infra.flags import flags

# Сигнатуры файлов (magic bytes) → MIME
_MAGIC = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"RIFF", "image/webp"),  # уточняем ниже
)


def sniff_mime(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


async def read_validated_upload(file: UploadFile) -> tuple[bytes, str, str]:
    """
    Читает UploadFile с проверками. Возвращает (bytes, content_type, extension).
    No-op проверок, если CITYVIBE_UPLOAD_VALIDATION_ENABLED=false (кроме пустого файла).
    """
    data = await file.read()
    f = flags()
    if not data:
        raise CoreException(message="Пустой файл", reason=ERR_REASON_VALIDATION)

    declared = (file.content_type or "").split(";")[0].strip().lower() or "application/octet-stream"
    ext = (file.filename or "file.bin").rsplit(".", 1)[-1].lower()

    if not f.upload_validation:
        return data, declared, ext

    if len(data) > f.upload_max_bytes:
        raise CoreException(
            message=f"Файл слишком большой (max {f.upload_max_bytes} bytes)",
            reason=ERR_REASON_VALIDATION,
        )

    sniffed = sniff_mime(data)
    effective = sniffed or declared
    if effective == "image/jpg":
        effective = "image/jpeg"

    allowed = set(f.upload_allowed_mime) | {"image/jpg"}
    if effective not in allowed and declared not in allowed:
        raise CoreException(
            message=f"MIME '{effective}' не разрешён. Allowed: {sorted(f.upload_allowed_mime)}",
            reason=ERR_REASON_VALIDATION,
        )

    if sniffed:
        effective = sniffed
        ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(sniffed, ext)

    return data, effective, ext


def validate_upload(param: str = "file"):
    """
    Декоратор: валидирует UploadFile-аргумент и кладёт байты в kwargs['_upload_bytes'] и т.п.
    Удобнее вызывать read_validated_upload явно в хендлере — декоратор для краткости:

        @validate_upload()
        async def upload_avatar(..., file: UploadFile):
            data, ctype, ext = file.state.validated  # type: ignore
    """

    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            upload: UploadFile | None = kwargs.get(param)
            if upload is None:
                return await fn(*args, **kwargs)
            data, ctype, ext = await read_validated_upload(upload)
            # Сохраняем результат на объекте файла (без ломки сигнатуры)
            upload.state.validated = (data, ctype, ext)  # type: ignore[attr-defined]
            return await fn(*args, **kwargs)

        return wrapper

    return decorator
