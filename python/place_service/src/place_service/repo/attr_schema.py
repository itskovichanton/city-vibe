"""Репозиторий JSON Schema attrs."""

from __future__ import annotations

from typing import Optional, Protocol

from sqlalchemy import select
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.libs.entities.place import AttrSchema
from python.place_service.src.place_service.infra.orm.mappers import attr_schema_model_to_dto
from python.place_service.src.place_service.infra.orm.models import AttrSchemaModel


class AttrSchemaRepo(Protocol):
    async def list_all(self) -> list[AttrSchema]: ...

    async def get_by_category(self, category_code: str) -> Optional[AttrSchema]: ...


@bean
class AttrSchemaRepoImpl(AttrSchemaRepo):
    db: Database

    async def list_all(self) -> list[AttrSchema]:
        async with self.db.session() as session:
            stmt = (
                select(AttrSchemaModel)
                .where(AttrSchemaModel.deleted.is_(False))
                .order_by(AttrSchemaModel.category_code)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [attr_schema_model_to_dto(m) for m in rows]

    async def get_by_category(self, category_code: str) -> Optional[AttrSchema]:
        async with self.db.session() as session:
            stmt = select(AttrSchemaModel).where(
                AttrSchemaModel.category_code == category_code,
                AttrSchemaModel.deleted.is_(False),
            )
            model = (await session.execute(stmt)).scalar_one_or_none()
            return attr_schema_model_to_dto(model) if model else None
