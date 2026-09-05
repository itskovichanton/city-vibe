"""Use-cases: справочники мира для Миланы."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.milana_service.src.milana_service.agent.places_nl_search import PlacesNlSearchAgent


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
