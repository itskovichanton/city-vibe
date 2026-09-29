"""Use-cases: справочники мира для Миланы."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.milana_service.src.milana_service.agent.catalog_hybrid import CatalogHybridMatcher
from python.milana_service.src.milana_service.agent.places_nl_search import PlacesNlSearchAgent
from python.milana_service.src.milana_service.entities.request import MilanaCatalogMatchRequest


class GetMilanaWorldUseCase(Protocol):
    async def execute(self) -> Any:
        ...


class ListMilanaCitiesUseCase(Protocol):
    async def execute(self) -> Any:
        ...


class ListMilanaCategoriesUseCase(Protocol):
    async def execute(self) -> Any:
        ...


class ListMilanaProductCategoriesUseCase(Protocol):
    async def execute(self) -> Any:
        ...


class GetMilanaAttrSchemaUseCase(Protocol):
    async def execute(self, category_code: str) -> Any:
        ...


class ListMilanaCatalogsUseCase(Protocol):
    async def execute(self) -> Any:
        ...


class MatchMilanaCatalogUseCase(Protocol):
    async def execute(self, request: MilanaCatalogMatchRequest) -> Any:
        ...


@bean
class GetMilanaWorldUseCaseImpl(GetMilanaWorldUseCase):
    places_nl_agent: PlacesNlSearchAgent

    async def execute(self) -> Any:
        return await self.places_nl_agent.world_digest()


@bean
class ListMilanaCitiesUseCaseImpl(ListMilanaCitiesUseCase):
    places_nl_agent: PlacesNlSearchAgent

    async def execute(self) -> Any:
        return await self.places_nl_agent.places.list_cities_compact()


@bean
class ListMilanaCategoriesUseCaseImpl(ListMilanaCategoriesUseCase):
    places_nl_agent: PlacesNlSearchAgent

    async def execute(self) -> Any:
        return await self.places_nl_agent.places.list_categories_compact()


@bean
class ListMilanaProductCategoriesUseCaseImpl(ListMilanaProductCategoriesUseCase):
    places_nl_agent: PlacesNlSearchAgent

    async def execute(self) -> Any:
        return await self.places_nl_agent.places.list_product_categories_compact()


@bean
class GetMilanaAttrSchemaUseCaseImpl(GetMilanaAttrSchemaUseCase):
    places_nl_agent: PlacesNlSearchAgent

    async def execute(self, category_code: str) -> Any:
        try:
            return await self.places_nl_agent.places.get_attr_schema_compact(category_code)
        except CoreException:
            raise
        except Exception as e:
            raise CoreException(
                message=f"Schema для {category_code} не найдена: {e}",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            ) from e


@bean
class ListMilanaCatalogsUseCaseImpl(ListMilanaCatalogsUseCase):
    places_nl_agent: PlacesNlSearchAgent

    async def execute(self) -> Any:
        return await self.places_nl_agent.places.list_catalogs()


@bean
class MatchMilanaCatalogUseCaseImpl(MatchMilanaCatalogUseCase):
    catalog_matcher: CatalogHybridMatcher

    async def execute(self, request: MilanaCatalogMatchRequest) -> Any:
        catalog = request.catalog
        entity_type = request.entity_type
        if not catalog and not entity_type:
            raise CoreException(message="Нужен catalog или entity_type")
        return await self.catalog_matcher.match(
            request.prompt,
            catalog=catalog,
            entity_type=entity_type,
            fields=request.fields,
            limit=request.limit,
            effort=request.effort,
        )
