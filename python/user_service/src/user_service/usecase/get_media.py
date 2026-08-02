"""Use-case: отдача файла из S3 по ключу."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.libs.clients.infra.s3.storage import FileNotFoundInStorageError, FileStorage
from python.user_service.src.user_service.entities.common import MediaContent


class GetMediaUseCase(Protocol):
    async def execute(self, key: str) -> MediaContent:
        ...


@bean
class GetMediaUseCaseImpl(GetMediaUseCase):
    file_storage: FileStorage

    async def execute(self, key: str) -> MediaContent:
        normalized = (key or "").strip().lstrip("/")
        if not normalized or ".." in normalized.split("/"):
            raise CoreException(
                message="Некорректный путь к файлу",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )

        try:
            data, content_type = await self.file_storage.download(normalized)
        except FileNotFoundInStorageError as e:
            raise CoreException(
                message=f"Файл не найден: {normalized}",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            ) from e

        return MediaContent(data=data, content_type=content_type)
