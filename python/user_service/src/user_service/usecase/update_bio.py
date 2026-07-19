"""Use-case: сохранение развёрнутого bio (шаг 2 онбординга)."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)


from python.libs.clients.infra.events import EventBus
from python.libs.entities.events import UserUpdatedEvent
from python.user_service.src.user_service.entities.common import UpdateBioRequest, UserResponse
from python.user_service.src.user_service.infra.orm.mappers import user_dto_to_response
from python.user_service.src.user_service.repo.user import UserRepo

TOPIC_USER_UPDATED = "user.updated"


class UpdateBioUseCase(Protocol):
    async def execute(self, request: UpdateBioRequest) -> UserResponse:
        ...


@bean
class UpdateBioUseCaseImpl(UpdateBioUseCase):
    user_repo: UserRepo
    event_bus: EventBus

    async def execute(self, request: UpdateBioRequest) -> UserResponse:
        user = await self.user_repo.update_bio(request.user_id, request.long_bio)
        if user is None:
            raise CoreException(
                message=f"Пользователь id={request.user_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        await self.event_bus.publish(TOPIC_USER_UPDATED, UserUpdatedEvent(user=user))
        return user_dto_to_response(user)
