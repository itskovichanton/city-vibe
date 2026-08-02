"""Use-cases: города."""

from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.place_service.src.place_service.entities.common import CityResponse, NearestCityRequest
from python.place_service.src.place_service.infra.orm.mappers import city_dto_to_response
from python.place_service.src.place_service.repo.city import CityRepo


class ListCitiesUseCase(Protocol):
    async def execute(self) -> list[CityResponse]:
        ...


class GetNearestCityUseCase(Protocol):
    async def execute(self, request: NearestCityRequest) -> CityResponse:
        ...


class GetCityUseCase(Protocol):
    async def execute(self, city_id: int) -> CityResponse:
        ...


@bean
class ListCitiesUseCaseImpl(ListCitiesUseCase):
    city_repo: CityRepo

    async def execute(self) -> list[CityResponse]:
        cities = await self.city_repo.list_major()
        return [city_dto_to_response(c) for c in cities]


@bean
class GetNearestCityUseCaseImpl(GetNearestCityUseCase):
    city_repo: CityRepo

    async def execute(self, request: NearestCityRequest) -> CityResponse:
        found = await self.city_repo.find_nearest(request.lat, request.lng, major_only=True)
        if found is None:
            raise CoreException(
                message="Не удалось определить ближайший город",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        city, distance_m = found
        resp = city_dto_to_response(city)
        resp.distance_m = distance_m
        return resp


@bean
class GetCityUseCaseImpl(GetCityUseCase):
    city_repo: CityRepo

    async def execute(self, city_id: int) -> CityResponse:
        city = await self.city_repo.get_by_id(city_id)
        if city is None:
            raise CoreException(
                message=f"Город id={city_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return city_dto_to_response(city)
