"""Репозиторий городов."""

from typing import Optional, Protocol, Tuple

from sqlalchemy import select, text
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.libs.entities.city import City
from python.place_service.src.place_service.infra.orm.mappers import city_model_to_dto
from python.place_service.src.place_service.infra.orm.models import CityModel


class CityRepo(Protocol):
    """Контракт репозитория городов."""

    async def list_major(self, limit: int = 100) -> list[City]:
        ...

    async def get_by_id(self, city_id: int) -> Optional[City]:
        ...

    async def find_nearest(
        self,
        lat: float,
        lng: float,
        *,
        major_only: bool = True,
    ) -> Optional[Tuple[City, float]]:
        """Ближайший город к координатам (метры). None — если справочник пуст."""
        ...


@bean
class CityRepoImpl(CityRepo):
    """SQLAlchemy-реализация."""

    db: Database

    async def list_major(self, limit: int = 100) -> list[City]:
        async with self.db.session() as session:
            stmt = (
                select(CityModel)
                .where(CityModel.deleted.is_(False), CityModel.is_major.is_(True))
                .order_by(CityModel.sort_order, CityModel.name)
                .limit(limit)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [city_model_to_dto(m) for m in rows]

    async def get_by_id(self, city_id: int) -> Optional[City]:
        async with self.db.session() as session:
            model = await session.get(CityModel, city_id)
            if model is None or model.deleted:
                return None
            return city_model_to_dto(model)

    async def find_nearest(
        self,
        lat: float,
        lng: float,
        *,
        major_only: bool = True,
    ) -> Optional[Tuple[City, float]]:
        major_sql = "AND is_major = TRUE" if major_only else ""
        sql = text(
            f"""
            SELECT id,
                   earth_distance(
                       ll_to_earth(lat, lng),
                       ll_to_earth(:lat, :lng)
                   ) AS distance_m
            FROM cities
            WHERE deleted = FALSE
              AND lat IS NOT NULL
              AND lng IS NOT NULL
              {major_sql}
            ORDER BY distance_m ASC
            LIMIT 1
            """
        )
        async with self.db.session() as session:
            row = (await session.execute(sql, {"lat": lat, "lng": lng})).mappings().first()
            if row is None:
                return None
            model = await session.get(CityModel, int(row["id"]))
            if model is None or model.deleted:
                return None
            return city_model_to_dto(model), float(row["distance_m"])
