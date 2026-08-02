"""Use-case: служебный аккаунт Миланы (milana.user_id из config)."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.user_service.src.user_service.entities.common import UserResponse
from python.user_service.src.user_service.infra.orm.mappers import user_dto_to_response
from python.user_service.src.user_service.repo.user import UserRepo


class GetMilanaAccountUseCase(Protocol):
    async def execute(self) -> UserResponse:
        ...


@bean(milana_user_id=("milana.user_id", int, 40))
class GetMilanaAccountUseCaseImpl(GetMilanaAccountUseCase):
    user_repo: UserRepo

    def init(self, **kwargs):
        self.milana_user_id = int(kwargs.get("milana_user_id") or 40)

    async def execute(self) -> UserResponse:
        user = await self.user_repo.get_by_id(self.milana_user_id)
        if user is None:
            raise CoreException(
                message="Служебный аккаунт Миланы не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return user_dto_to_response(user)
