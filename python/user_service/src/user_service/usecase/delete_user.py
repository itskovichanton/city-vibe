"""Use-case: soft-delete пользователя."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.user_service.src.user_service.entities.common import DeleteUserRequest, DeleteUserResponse
from python.user_service.src.user_service.repo.user import UserRepo


class DeleteUserUseCase(Protocol):
    async def execute(self, request: DeleteUserRequest) -> DeleteUserResponse:
        ...


@bean
class DeleteUserUseCaseImpl(DeleteUserUseCase):
    user_repo: UserRepo

    async def execute(self, request: DeleteUserRequest) -> DeleteUserResponse:
        ok = await self.user_repo.soft_delete(request.user_id)
        if not ok:
            raise CoreException(
                message=f"Пользователь id={request.user_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return DeleteUserResponse(ok=True, user_id=request.user_id)
