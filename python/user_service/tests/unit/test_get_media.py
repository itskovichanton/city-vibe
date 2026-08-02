"""Юнит-тесты use-case get_media."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.user_service.src.user_service.entities.common import MediaContent
from python.user_service.src.user_service.usecase.get_media import GetMediaUseCaseImpl


@pytest.mark.asyncio
async def test_get_media_success():
    storage = AsyncMock()
    storage.download = AsyncMock(return_value=(b"png", "image/png"))

    uc = object.__new__(GetMediaUseCaseImpl)
    uc.file_storage = storage

    result = await uc.execute("avatars/5/abc.png")

    assert result == MediaContent(data=b"png", content_type="image/png")
    storage.download.assert_awaited_once_with("avatars/5/abc.png")


@pytest.mark.asyncio
async def test_get_media_rejects_path_traversal():
    uc = object.__new__(GetMediaUseCaseImpl)
    uc.file_storage = AsyncMock()

    with pytest.raises(CoreException):
        await uc.execute("avatars/../etc/passwd")
