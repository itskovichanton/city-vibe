"""
HTTP-клиент user-service (Spring-like: Protocol + @bean Impl).

Используем on_mbclient_api — тот же подход, что и для внутренних
микросервисов (см. mbulak_tools biofull / bioguard):
  - url / auth / lang из config.yml
  - logged session + request_id
  - разбор ответа через parse_response ({result}/{error})
"""

from __future__ import annotations

from typing import Any, Protocol

from src.mybootstrap_core_itskovichanton.utils import to_dict
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_fastapi_itskovichanton.client.http import on_mbclient_api

from python.libs.clients.domain.user_service.entities import CreateUserBody, UpdateBioBody

# Имя секции в config.yml → clients.user_service.url
api_call = on_mbclient_api(_name="clients.user_service")


class UserServiceClient(Protocol):
    """Контракт клиента user-service (инжектить именно его)."""

    def health(self) -> Any:
        """Healthcheck сервиса."""
        ...

    def create_user(self, body: CreateUserBody) -> Any:
        """Создать пользователя (онбординг, шаг 1)."""
        ...

    def get_user(self, user_id: int) -> Any:
        """Получить профиль по id."""
        ...

    def update_bio(self, user_id: int, body: UpdateBioBody) -> Any:
        """Обновить развёрнутое bio (онбординг, шаг 2)."""
        ...

    def complete_onboarding(self, user_id: int) -> Any:
        """Завершить онбординг (шаг 3)."""
        ...

    def upload_avatar(
        self,
        user_id: int,
        filename: str,
        data: bytes,
        content_type: str = "image/jpeg",
    ) -> Any:
        """Загрузить аватарку и привязать к профилю."""
        ...

    def delete_user(self, user_id: int) -> Any:
        """Soft-delete пользователя (компенсация saga)."""
        ...


@bean
class UserServiceClientImpl(UserServiceClient):
    """
    Реализация UserServiceClient через on_mbclient_api + requests session.

    Конфиг (MBClientConfig) читается из config.yml:
      clients:
        user_service:
          url: http://localhost:8081
    """

    @api_call
    def health(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/health", timeout=30, headers=headers)

    @api_call
    def create_user(self, body: CreateUserBody, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/users",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def get_user(self, user_id: int, session=None, url=None, headers=None):
        return session.get(url=f"{url}/users/{user_id}", timeout=30, headers=headers)

    @api_call
    def update_bio(self, user_id: int, body: UpdateBioBody, session=None, url=None, headers=None):
        return session.put(
            url=f"{url}/users/{user_id}/bio",
            timeout=30,
            headers=headers,
            json=to_dict(body, remove_none_values=True),
        )

    @api_call
    def complete_onboarding(self, user_id: int, session=None, url=None, headers=None):
        return session.post(
            url=f"{url}/users/{user_id}/onboarding/complete",
            timeout=30,
            headers=headers,
        )

    @api_call
    def upload_avatar(
        self,
        user_id: int,
        filename: str,
        data: bytes,
        content_type: str = "image/jpeg",
        session=None,
        url=None,
        headers=None,
    ):
        return session.post(
            url=f"{url}/users/{user_id}/avatar",
            timeout=60,
            headers=headers,
            files={"file": (filename, data, content_type)},
        )

    @api_call
    def delete_user(self, user_id: int, session=None, url=None, headers=None):
        return session.delete(url=f"{url}/users/{user_id}", timeout=30, headers=headers)
