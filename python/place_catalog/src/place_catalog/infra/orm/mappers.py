"""Маппинг ORM ↔ DTO."""

from python.libs.entities.city import City
from python.libs.entities.geo import GeoLocation
from python.libs.utils.translit import slugify
from python.place_catalog.src.place_catalog.entities.common import CityResponse
from python.place_catalog.src.place_catalog.infra.orm.models import CityModel

__all__ = ["slugify", "city_model_to_dto", "city_dto_to_response"]


def city_model_to_dto(model: CityModel) -> City:
    return City(
        id=model.id,
        deleted=model.deleted,
        created_at=model.created_at,
        updated_at=model.updated_at,
        name=model.name,
        slug=model.slug,
        about=model.about or "",
        geo=GeoLocation.of(model.lat, model.lng),
        region=model.region or "",
        is_major=model.is_major,
        sort_order=model.sort_order,
    )


def city_dto_to_response(city: City) -> CityResponse:
    return CityResponse(
        id=city.id,
        name=city.name,
        slug=city.slug,
        region=city.region,
        geo=city.geo,
        is_major=city.is_major,
        sort_order=city.sort_order,
        about=city.about,
        deleted=city.deleted,
        created_at=city.created_at,
        updated_at=city.updated_at,
    )
