"""Use-case: публичный аккаунт Миланы для мобильного клиента."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.domain.user_service.client import UserServiceClient


class GetMilanaAccountUseCase(Protocol):
    async def execute(self) -> Any:
        ...


@bean
class GetMilanaAccountUseCaseImpl(GetMilanaAccountUseCase):
    user_client: UserServiceClient

    async def execute(self) -> Any:
        return self.user_client.get_milana_account()
