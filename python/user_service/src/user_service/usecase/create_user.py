"""Use-case: создание пользователя (шаг 1 онбординга)."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.entities.events import UserCreatedEvent
from python.libs.infra.outbox import Outbox
from python.user_service.src.user_service.entities.common import CreateUserRequest, UserResponse
from python.user_service.src.user_service.infra.orm.mappers import user_dto_to_response
from python.user_service.src.user_service.repo.user import UserRepo

TOPIC_USER_CREATED = "user.created"


class CreateUserUseCase(Protocol):
    async def execute(self, request: CreateUserRequest) -> UserResponse:
        ...


@bean
class CreateUserUseCaseImpl(CreateUserUseCase):
    user_repo: UserRepo
    outbox: Outbox

    async def execute(self, request: CreateUserRequest) -> UserResponse:
        user = await self.user_repo.create(
            name=request.name,
            age=request.age,
            short_bio=request.short_bio,
            favorite_categories=request.favorite_categories,
            avatar_url=request.avatar_url,
        )
        # Outbox: при CITYVIBE_OUTBOX_ENABLED=false сразу уйдёт в EventBus
        await self.outbox.publish(TOPIC_USER_CREATED, UserCreatedEvent(user=user))
        return user_dto_to_response(user)
