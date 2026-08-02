"""Use-case: NL-поиск мест через ИИ-агента Милану."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.milana_service.src.milana_service.agent.places_nl_search import PlacesNlSearchAgent
from python.milana_service.src.milana_service.entities.request import MilanaPlacesSearchRequest


class MilanaPlacesSearchUseCase(Protocol):
    async def execute(self, request: MilanaPlacesSearchRequest) -> dict[str, Any]:
        ...


@bean
class MilanaPlacesSearchUseCaseImpl(MilanaPlacesSearchUseCase):
    places_nl_agent: PlacesNlSearchAgent

    async def execute(self, request: MilanaPlacesSearchRequest) -> dict[str, Any]:
        result = await self.places_nl_agent.run(request)
        return result.model_dump()
