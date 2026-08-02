"""Use-case: публичный аккаунт Миланы для мобильного клиента."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.domain.user_service.client import UserServiceClient


class GetMilanaAccountUseCase(Protocol):
    async def execute(self) -> Any:
        ...


@bean(milana_user_id=("milana.user_id", int, 40))
class GetMilanaAccountUseCaseImpl(GetMilanaAccountUseCase):
    user_client: UserServiceClient

    def init(self, **kwargs):
        self.milana_user_id = int(kwargs.get("milana_user_id") or 40)

    async def execute(self) -> Any:
        return self.user_client.get_user(self.milana_user_id)
