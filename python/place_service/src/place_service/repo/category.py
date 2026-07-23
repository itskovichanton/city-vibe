"""Репозиторий категорий мест."""

from __future__ import annotations

from typing import Optional, Protocol

from sqlalchemy import select
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.libs.entities.place import PlaceCategoryInfo
from python.place_service.src.place_service.infra.orm.mappers import category_model_to_dto
from python.place_service.src.place_service.infra.orm.models import PlaceCategoryModel


class CategoryRepo(Protocol):
    async def list_active(self) -> list[PlaceCategoryInfo]: ...

    async def get_by_code(self, code: str) -> Optional[PlaceCategoryInfo]: ...


@bean
class CategoryRepoImpl(CategoryRepo):
    db: Database

    async def list_active(self) -> list[PlaceCategoryInfo]:
        async with self.db.session() as session:
            stmt = (
                select(PlaceCategoryModel)
                .where(PlaceCategoryModel.deleted.is_(False), PlaceCategoryModel.is_active.is_(True))
                .order_by(PlaceCategoryModel.sort_order, PlaceCategoryModel.title)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [category_model_to_dto(m) for m in rows]

    async def get_by_code(self, code: str) -> Optional[PlaceCategoryInfo]:
        async with self.db.session() as session:
            stmt = select(PlaceCategoryModel).where(
                PlaceCategoryModel.code == code,
                PlaceCategoryModel.deleted.is_(False),
            )
            model = (await session.execute(stmt)).scalar_one_or_none()
            return category_model_to_dto(model) if model else None
