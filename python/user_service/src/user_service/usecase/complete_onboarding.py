"""Use-case: завершение онбординга (шаг 3)."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)


from python.libs.clients.infra.events import EventBus
from python.libs.entities.events import UserOnboardingCompletedEvent
from python.user_service.src.user_service.entities.common import CompleteOnboardingRequest, UserResponse
from python.user_service.src.user_service.infra.orm.mappers import user_dto_to_response
from python.user_service.src.user_service.repo.user import UserRepo

TOPIC_ONBOARDING_COMPLETED = "user.onboarding.completed"


class CompleteOnboardingUseCase(Protocol):
    async def execute(self, request: CompleteOnboardingRequest) -> UserResponse:
        ...


@bean
class CompleteOnboardingUseCaseImpl(CompleteOnboardingUseCase):
    user_repo: UserRepo
    event_bus: EventBus

    async def execute(self, request: CompleteOnboardingRequest) -> UserResponse:
        user = await self.user_repo.complete_onboarding(request.user_id)
        if user is None:
            raise CoreException(
                message=f"Пользователь id={request.user_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        # Recommendation / AI-сервисы подписаны на этот топик
        await self.event_bus.publish(
            TOPIC_ONBOARDING_COMPLETED,
            UserOnboardingCompletedEvent(user=user),
        )
        return user_dto_to_response(user)
