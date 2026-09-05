"""Use-case: многокритериальный поиск мест."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.place_service.src.place_service.entities.common import SearchPlacesRequest
from python.place_service.src.place_service.infra.orm.mappers import place_to_api_dict
from python.place_service.src.place_service.repo.attr_schema import AttrSchemaRepo
from python.place_service.src.place_service.repo.category import CategoryRepo
from python.place_service.src.place_service.repo.city import CityRepo
from python.place_service.src.place_service.repo.place_search import PlaceSearchRepo


class SearchPlacesUseCase(Protocol):
    async def execute(self, request: SearchPlacesRequest) -> dict[str, Any]:
        ...


@bean
class SearchPlacesUseCaseImpl(SearchPlacesUseCase):
    category_repo: CategoryRepo
    city_repo: CityRepo
    attr_schema_repo: AttrSchemaRepo
    place_search_repo: PlaceSearchRepo

    async def execute(self, request: SearchPlacesRequest) -> dict[str, Any]:
        if request.category:
            cat = await self.category_repo.get_by_code(request.category)
            if cat is None:
                raise CoreException(message=f"Категория {request.category} не найдена в справочнике")
        city = await self.city_repo.get_by_id(request.city_id)
        if city is None:
            raise CoreException(
                message=f"Город id={request.city_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        if request.attrs:
            schema = await self.attr_schema_repo.get_by_category(request.category)
            if schema is None:
                raise CoreException(message=f"JSON Schema для {request.category} не найдена")
            allowed = set((schema.json_schema.get("properties") or {}).keys())
            unknown = [k for k in request.attrs if k not in allowed]
            if unknown:
                raise CoreException(
                    message=f"Неизвестные поля attrs для {request.category}: {', '.join(unknown)}"
                )

        result = await self.place_search_repo.search(request)
        items = []
        for place in result.items:
            item = place_to_api_dict(place)
            if place.id in result.distances_m:
                item["distance_m"] = round(result.distances_m[place.id], 1)
            items.append(item)
        return {
            "items": items,
            "total": result.total,
            "page": result.page,
            "limit": result.limit,
            "pages": (result.total + result.limit - 1) // result.limit if result.limit else 0,
        }
