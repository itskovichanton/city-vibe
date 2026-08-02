"""Юнит-тесты use-case delete_user."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from python.user_service.src.user_service.entities.common import DeleteUserRequest
from python.user_service.src.user_service.usecase.delete_user import DeleteUserUseCaseImpl


@pytest.mark.asyncio
async def test_delete_user_success():
    repo = AsyncMock()
    repo.soft_delete = AsyncMock(return_value=True)

    uc = object.__new__(DeleteUserUseCaseImpl)
    uc.user_repo = repo

    result = await uc.execute(DeleteUserRequest(user_id=42))

    assert result.ok is True
    assert result.user_id == 42
    repo.soft_delete.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_delete_user_not_found_raises():
    repo = AsyncMock()
    repo.soft_delete = AsyncMock(return_value=False)

    uc = object.__new__(DeleteUserUseCaseImpl)
    uc.user_repo = repo

    from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

    with pytest.raises(CoreException):
        await uc.execute(DeleteUserRequest(user_id=999))
