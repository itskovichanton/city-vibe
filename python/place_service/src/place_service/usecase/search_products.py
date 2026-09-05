"""Use-case: многокритериальный поиск продуктов."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.place_service.src.place_service.entities.search import ProductSearchRequest
from python.place_service.src.place_service.infra.orm.mappers import (
    compact_place_dict,
    product_to_api_dict,
)
from python.place_service.src.place_service.repo.city import CityRepo
from python.place_service.src.place_service.repo.place import PlaceRepo
from python.place_service.src.place_service.repo.product_category import ProductCategoryRepo
from python.place_service.src.place_service.repo.product_search import ProductSearchRepo


class SearchProductsUseCase(Protocol):
    async def execute(self, request: ProductSearchRequest) -> dict[str, Any]:
        ...


@bean
class SearchProductsUseCaseImpl(SearchProductsUseCase):
    product_category_repo: ProductCategoryRepo
    city_repo: CityRepo
    place_repo: PlaceRepo
    product_search_repo: ProductSearchRepo

    async def execute(self, request: ProductSearchRequest) -> dict[str, Any]:
        if request.category:
            cat = await self.product_category_repo.get_by_code(request.category)
            if cat is None:
                raise CoreException(message=f"Категория продукта {request.category} не найдена")
        city = await self.city_repo.get_by_id(request.city_id)
        if city is None:
            raise CoreException(
                message=f"Город id={request.city_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        result = await self.product_search_repo.search(request)
        items = []
        for product in result.items:
            place = await self.place_repo.get_by_id(product.place_id)
            items.append(
                product_to_api_dict(
                    product,
                    place=compact_place_dict(place) if place else None,
                    distance_m=result.distances_m.get(product.id),
                )
            )
        return {
            "items": items,
            "total": result.total,
            "page": result.page,
            "limit": result.limit,
            "pages": (result.total + result.limit - 1) // result.limit if result.limit else 0,
        }
