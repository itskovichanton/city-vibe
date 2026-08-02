"""Use-case: обновление профиля (имя, категории) — онбординг, шаг 1."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.libs.entities.events import UserUpdatedEvent
from python.libs.infra.outbox import Outbox
from python.user_service.src.user_service.entities.common import UpdateProfileRequest, UserResponse
from python.user_service.src.user_service.infra.orm.mappers import user_dto_to_response
from python.user_service.src.user_service.repo.user import UserRepo

TOPIC_USER_UPDATED = "user.updated"


class UpdateProfileUseCase(Protocol):
    async def execute(self, request: UpdateProfileRequest) -> UserResponse:
        ...


@bean
class UpdateProfileUseCaseImpl(UpdateProfileUseCase):
    user_repo: UserRepo
    outbox: Outbox

    async def execute(self, request: UpdateProfileRequest) -> UserResponse:
        user = await self.user_repo.update_profile(
            request.user_id,
            name=request.name,
            favorite_categories=request.favorite_categories,
        )
        if user is None:
            raise CoreException(
                message=f"Пользователь id={request.user_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        await self.outbox.publish(TOPIC_USER_UPDATED, UserUpdatedEvent(user=user))
        return user_dto_to_response(user)
