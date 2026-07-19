"""Use-case: получение профиля по id."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.user_service.src.user_service.entities.common import UserResponse
from python.user_service.src.user_service.infra.orm.mappers import user_dto_to_response
from python.user_service.src.user_service.repo.user import UserRepo


class GetUserUseCase(Protocol):
    async def execute(self, user_id: int) -> UserResponse:
        ...


@bean
class GetUserUseCaseImpl(GetUserUseCase):
    user_repo: UserRepo

    async def execute(self, user_id: int) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise CoreException(
                message=f"Пользователь id={user_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return user_dto_to_response(user)
