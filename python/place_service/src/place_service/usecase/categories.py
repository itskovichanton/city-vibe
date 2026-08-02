"""Use-case: справочник категорий мест."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.place_service.src.place_service.infra.orm.mappers import category_to_api
from python.place_service.src.place_service.repo.category import CategoryRepo


class ListCategoriesUseCase(Protocol):
    async def execute(self, _call: None = None) -> list[dict[str, Any]]:
        ...


@bean
class ListCategoriesUseCaseImpl(ListCategoriesUseCase):
    category_repo: CategoryRepo

    async def execute(self, _call: None = None) -> list[dict[str, Any]]:
        items = await self.category_repo.list_active()
        return [category_to_api(c) for c in items]
