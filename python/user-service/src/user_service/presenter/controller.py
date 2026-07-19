"""Контроллер: связывает HTTP-слой с use-case через ActionRunner."""

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.pipeline import ActionRunner, Result

from user_service.entities.common import (
    CompleteOnboardingRequest,
    CreateUserRequest,
    UpdateBioRequest,
)
from user_service.usecase.complete_onboarding import CompleteOnboardingUseCase
from user_service.usecase.create_user import CreateUserUseCase
from user_service.usecase.get_user import GetUserUseCase
from user_service.usecase.update_bio import UpdateBioUseCase


@bean
class UserController:
    """Тонкий слой: валидация входа — в FastAPI, бизнес-логика — в use-case."""

    action_runner: ActionRunner
    create_user_uc: CreateUserUseCase
    update_bio_uc: UpdateBioUseCase
    complete_onboarding_uc: CompleteOnboardingUseCase
    get_user_uc: GetUserUseCase

    async def create_user(self, request: CreateUserRequest) -> Result:
        return await self.action_runner.run(self.create_user_uc.execute, call=request)

    async def update_bio(self, request: UpdateBioRequest) -> Result:
        return await self.action_runner.run(self.update_bio_uc.execute, call=request)

    async def complete_onboarding(self, request: CompleteOnboardingRequest) -> Result:
        return await self.action_runner.run(self.complete_onboarding_uc.execute, call=request)

    async def get_user(self, user_id: int) -> Result:
        return await self.action_runner.run(self.get_user_uc.execute, call=user_id)
