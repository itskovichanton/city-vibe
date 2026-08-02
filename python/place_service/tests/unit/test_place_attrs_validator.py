"""Юнит-тесты PlaceAttrsValidator."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from python.place_service.src.place_service.usecase.place_attrs import PlaceAttrsValidatorImpl


@pytest.mark.asyncio
async def test_resolve_and_validate_success():
    category_repo = AsyncMock()
    category_repo.get_by_code = AsyncMock(return_value=object())

    schema = AsyncMock()
    schema.json_schema = {
        "type": "object",
        "properties": {"has_wifi": {"type": "boolean"}},
    }
    attr_schema_repo = AsyncMock()
    attr_schema_repo.get_by_category = AsyncMock(return_value=schema)

    validator = object.__new__(PlaceAttrsValidatorImpl)
    validator.category_repo = category_repo
    validator.attr_schema_repo = attr_schema_repo

    result = await validator.resolve_and_validate("bars", {"has_wifi": True})
    assert result == {"has_wifi": True}


@pytest.mark.asyncio
async def test_resolve_unknown_category_raises():
    validator = object.__new__(PlaceAttrsValidatorImpl)
    validator.category_repo = AsyncMock()
    validator.attr_schema_repo = AsyncMock()

    from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

    with pytest.raises(CoreException, match="Неизвестная категория"):
        await validator.resolve_and_validate("no_such", {})
