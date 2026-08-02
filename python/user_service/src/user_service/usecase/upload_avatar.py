"""Use-case: загрузка аватара в S3 и обновление профиля."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.libs.clients.infra.s3 import FileStorage
from python.libs.entities.events import UserUpdatedEvent
from python.libs.infra.outbox import Outbox
from python.user_service.src.user_service.entities.common import UploadAvatarRequest, UserResponse
from python.user_service.src.user_service.infra.orm.mappers import user_dto_to_response
from python.user_service.src.user_service.repo.user import UserRepo

TOPIC_USER_UPDATED = "user.updated"


class UploadAvatarUseCase(Protocol):
    async def execute(self, request: UploadAvatarRequest) -> UserResponse:
        ...


@bean
class UploadAvatarUseCaseImpl(UploadAvatarUseCase):
    user_repo: UserRepo
    file_storage: FileStorage
    outbox: Outbox

    async def execute(self, request: UploadAvatarRequest) -> UserResponse:
        user = await self.user_repo.get_by_id(request.user_id)
        if user is None:
            raise CoreException(
                message=f"Пользователь id={request.user_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )

        url = await self.file_storage.upload(
            request.data,
            content_type=request.content_type,
            key_prefix=f"avatars/{request.user_id}",
            extension=request.extension,
        )
        user.avatar_url = url
        saved = await self.user_repo.save(user)
        await self.outbox.publish(TOPIC_USER_UPDATED, UserUpdatedEvent(user=saved))
        return user_dto_to_response(saved)
