"""Юнит-тесты use-case upload_avatar."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from python.libs.entities.user import Gender, Status, User, UserRole
from python.user_service.src.user_service.entities.common import UploadAvatarRequest
from python.user_service.src.user_service.usecase.upload_avatar import UploadAvatarUseCaseImpl


@pytest.mark.asyncio
async def test_upload_avatar_success():
    user = User(
        id=5,
        deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        status=Status.ACTIVE,
        name="Тест",
        gender=Gender.MALE,
        role=UserRole.REGULAR,
    )
    saved = User(
        id=5,
        deleted=False,
        created_at=user.created_at,
        updated_at=user.updated_at,
        status=Status.ACTIVE,
        name="Тест",
        gender=Gender.MALE,
        role=UserRole.REGULAR,
        avatar_url="http://localhost:9000/city-vibe/avatars/5/abc.png",
    )

    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)
    repo.save = AsyncMock(return_value=saved)

    storage = AsyncMock()
    storage.upload = AsyncMock(return_value=saved.avatar_url)

    outbox = AsyncMock()
    uc = object.__new__(UploadAvatarUseCaseImpl)
    uc.user_repo = repo
    uc.file_storage = storage
    uc.outbox = outbox

    result = await uc.execute(
        UploadAvatarRequest(
            user_id=5,
            data=b"\x89PNG\r\n",
            content_type="image/png",
            extension=".png",
        )
    )

    assert result.avatar_url == saved.avatar_url
    storage.upload.assert_awaited_once()
    repo.save.assert_awaited_once()
    outbox.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_avatar_not_found_raises():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)

    uc = object.__new__(UploadAvatarUseCaseImpl)
    uc.user_repo = repo
    uc.file_storage = AsyncMock()
    uc.outbox = AsyncMock()

    from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

    with pytest.raises(CoreException):
        await uc.execute(
            UploadAvatarRequest(
                user_id=999,
                data=b"x",
                content_type="image/png",
                extension=".png",
            )
        )
