"""Use-case: создание пользователя (шаг 1 онбординга)."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.infra.events import EventBus
from python.libs.entities.events import UserCreatedEvent
from user_service.entities.common import CreateUserRequest, UserResponse
from user_service.infra.orm.mappers import user_dto_to_response
from user_service.repo.user import UserRepo

# Имя топика для события создания пользователя
TOPIC_USER_CREATED = "user.created"


class CreateUserUseCase(Protocol):
    async def execute(self, request: CreateUserRequest) -> UserResponse:
        ...


@bean
class CreateUserUseCaseImpl(CreateUserUseCase):
    user_repo: UserRepo
    event_bus: EventBus

    async def execute(self, request: CreateUserRequest) -> UserResponse:
        user = await self.user_repo.create(
            name=request.name,
            age=request.age,
            short_bio=request.short_bio,
            favorite_categories=request.favorite_categories,
            avatar_url=request.avatar_url,
        )
        # Уведомляем остальные сервисы через шину событий
        await self.event_bus.publish(TOPIC_USER_CREATED, UserCreatedEvent(user=user))
        return user_dto_to_response(user)
