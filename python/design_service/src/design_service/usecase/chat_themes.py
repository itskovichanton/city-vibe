"""Use-cases: темы чата."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.design_service.src.design_service.infra.orm.mappers import theme_to_api
from python.design_service.src.design_service.repo.chat_theme import ChatThemeRepo


class ListChatThemesUseCase(Protocol):
    async def execute(self) -> list[dict[str, Any]]:
        ...


class GetDefaultChatThemeUseCase(Protocol):
    async def execute(self) -> dict[str, Any]:
        ...


class GetChatThemeUseCase(Protocol):
    async def execute(self, theme_id: int) -> dict[str, Any]:
        ...


@bean
class ListChatThemesUseCaseImpl(ListChatThemesUseCase):
    chat_theme_repo: ChatThemeRepo

    async def execute(self) -> list[dict[str, Any]]:
        themes = await self.chat_theme_repo.list_all()
        return [theme_to_api(t) for t in themes]


@bean
class GetDefaultChatThemeUseCaseImpl(GetDefaultChatThemeUseCase):
    chat_theme_repo: ChatThemeRepo

    async def execute(self) -> dict[str, Any]:
        theme = await self.chat_theme_repo.get_by_code("default")
        if theme is None:
            raise CoreException(
                message="default chat theme не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return theme_to_api(theme)


@bean
class GetChatThemeUseCaseImpl(GetChatThemeUseCase):
    chat_theme_repo: ChatThemeRepo

    async def execute(self, theme_id: int) -> dict[str, Any]:
        theme = await self.chat_theme_repo.get_by_id(theme_id)
        if theme is None:
            raise CoreException(
                message=f"Chat theme id={theme_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return theme_to_api(theme)
