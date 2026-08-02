"""Юнит-тесты use-case update_profile."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from datetime import datetime, timezone

import pytest

from python.libs.entities.place import PlaceCategory
from python.libs.entities.user import Gender, Status, User, UserRole
from python.user_service.src.user_service.entities.common import UpdateProfileRequest
from python.user_service.src.user_service.usecase.update_profile import UpdateProfileUseCaseImpl


@pytest.mark.asyncio
async def test_update_profile_use_case_publishes_event():
    user = User(
        id=7,
        deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        status=Status.ACTIVE,
        name="Новое имя",
        gender=Gender.MALE,
        role=UserRole.REGULAR,
        favorite_categories=[PlaceCategory.BARS],
    )

    repo = AsyncMock()
    repo.update_profile = AsyncMock(return_value=user)

    outbox = AsyncMock()
    uc = object.__new__(UpdateProfileUseCaseImpl)
    uc.user_repo = repo
    uc.outbox = outbox

    result = await uc.execute(
        UpdateProfileRequest(
            user_id=7,
            name="Новое имя",
            favorite_categories=[PlaceCategory.BARS],
        )
    )

    assert result.name == "Новое имя"
    repo.update_profile.assert_awaited_once()
    outbox.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_profile_not_found_raises():
    repo = AsyncMock()
    repo.update_profile = AsyncMock(return_value=None)

    uc = object.__new__(UpdateProfileUseCaseImpl)
    uc.user_repo = repo
    uc.outbox = MagicMock()

    from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

    with pytest.raises(CoreException):
        await uc.execute(UpdateProfileRequest(user_id=999, name="X"))
