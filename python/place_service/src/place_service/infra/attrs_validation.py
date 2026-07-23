"""Строгая валидация Place.attrs по JSON Schema категории."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator
from src.mybootstrap_mvc_itskovichanton.exceptions import ERR_REASON_VALIDATION, CoreException


def validate_attrs(attrs: dict[str, Any] | None, schema: dict[str, Any]) -> dict[str, Any]:
    data = attrs or {}
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        messages = [f"{'/'.join(str(p) for p in e.path) or '$'}: {e.message}" for e in errors]
        raise CoreException(
            message="attrs не соответствуют JSON Schema: " + "; ".join(messages[:5]),
            reason=ERR_REASON_VALIDATION,
        )
    return data
