"""Use-case: справочник категорий продуктов."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.place_service.src.place_service.infra.orm.mappers import product_category_to_api
from python.place_service.src.place_service.repo.product_category import ProductCategoryRepo


class ListProductCategoriesUseCase(Protocol):
    async def execute(self, _call: None = None) -> list[dict[str, Any]]:
        ...


@bean
class ListProductCategoriesUseCaseImpl(ListProductCategoriesUseCase):
    product_category_repo: ProductCategoryRepo

    async def execute(self, _call: None = None) -> list[dict[str, Any]]:
        items = await self.product_category_repo.list_active()
        return [product_category_to_api(c) for c in items]
