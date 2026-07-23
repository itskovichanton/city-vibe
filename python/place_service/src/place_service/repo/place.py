"""Репозиторий мест."""

from __future__ import annotations

from typing import Any, Optional, Protocol

from sqlalchemy import select
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.libs.entities.place import Place
from python.place_service.src.place_service.infra.orm.mappers import place_model_to_dto, schedule_to_json
from python.place_service.src.place_service.infra.orm.models import PlaceModel


class PlaceRepo(Protocol):
    async def get_by_id(self, place_id: int) -> Optional[Place]: ...

    async def list(
        self,
        *,
        owner_id: int | None = None,
        category: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        limit: int = 100,
    ) -> list[Place]: ...

    async def create(self, **kwargs: Any) -> Place: ...

    async def update(self, place_id: int, **kwargs: Any) -> Optional[Place]: ...

    async def soft_delete(self, place_id: int) -> bool: ...


@bean
class PlaceRepoImpl(PlaceRepo):
    db: Database

    async def get_by_id(self, place_id: int) -> Optional[Place]:
        async with self.db.session() as session:
            model = await session.get(PlaceModel, place_id)
            if model is None or model.deleted:
                return None
            return place_model_to_dto(model)

    async def list(
        self,
        *,
        owner_id: int | None = None,
        category: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        limit: int = 100,
    ) -> list[Place]:
        async with self.db.session() as session:
            stmt = select(PlaceModel).where(PlaceModel.deleted.is_(False))
            if owner_id is not None:
                stmt = stmt.where(PlaceModel.owner_id == owner_id)
            if category:
                stmt = stmt.where(PlaceModel.category_code == category)
            if bbox:
                min_lat, min_lng, max_lat, max_lng = bbox
                stmt = stmt.where(
                    PlaceModel.lat >= min_lat,
                    PlaceModel.lat <= max_lat,
                    PlaceModel.lng >= min_lng,
                    PlaceModel.lng <= max_lng,
                )
            stmt = stmt.order_by(PlaceModel.id.desc()).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()
            return [place_model_to_dto(m) for m in rows]

    async def create(self, **kwargs: Any) -> Place:
        async with self.db.session() as session:
            schedule = kwargs.pop("schedule", None)
            model = PlaceModel(
                name=kwargs["name"],
                about=kwargs["about"],
                category_code=kwargs["category_code"],
                owner_id=kwargs["owner_id"],
                city_id=kwargs.get("city_id"),
                lat=kwargs["lat"],
                lng=kwargs["lng"],
                attrs=kwargs.get("attrs") or {},
                schedule=schedule_to_json(schedule) if schedule is not None else None,
                pin_style_id=kwargs.get("pin_style_id"),
                chat_theme_id=kwargs.get("chat_theme_id"),
                contacts=kwargs.get("contacts") or [],
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return place_model_to_dto(model)

    async def update(self, place_id: int, **kwargs: Any) -> Optional[Place]:
        async with self.db.session() as session:
            model = await session.get(PlaceModel, place_id)
            if model is None or model.deleted:
                return None
            for key, value in kwargs.items():
                if value is None and key not in ("schedule", "pin_style_id", "chat_theme_id", "city_id", "attrs"):
                    continue
                if key == "schedule":
                    model.schedule = schedule_to_json(value)
                elif key == "lat":
                    model.lat = value
                elif key == "lng":
                    model.lng = value
                elif hasattr(model, key):
                    setattr(model, key, value)
            await session.commit()
            await session.refresh(model)
            return place_model_to_dto(model)

    async def soft_delete(self, place_id: int) -> bool:
        async with self.db.session() as session:
            model = await session.get(PlaceModel, place_id)
            if model is None or model.deleted:
                return False
            model.deleted = True
            await session.commit()
            return True
