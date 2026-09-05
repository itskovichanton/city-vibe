"""Репозиторий продуктов."""

from __future__ import annotations

from typing import Any, Optional, Protocol

from sqlalchemy import select
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.libs.entities.place import Product
from python.place_service.src.place_service.infra.orm.mappers import (
    product_model_to_dto,
    schedule_to_json,
)
from python.place_service.src.place_service.infra.orm.models import ProductModel


class ProductRepo(Protocol):
    async def get_by_id(self, product_id: int) -> Optional[Product]: ...

    async def list(
        self,
        *,
        place_id: int | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[Product]: ...

    async def create(self, **kwargs: Any) -> Product: ...

    async def update(self, product_id: int, **kwargs: Any) -> Optional[Product]: ...

    async def soft_delete(self, product_id: int) -> bool: ...


@bean
class ProductRepoImpl(ProductRepo):
    db: Database

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        async with self.db.session() as session:
            model = await session.get(ProductModel, product_id)
            if model is None or model.deleted:
                return None
            return product_model_to_dto(model)

    async def list(
        self,
        *,
        place_id: int | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[Product]:
        async with self.db.session() as session:
            stmt = select(ProductModel).where(ProductModel.deleted.is_(False))
            if place_id is not None:
                stmt = stmt.where(ProductModel.place_id == place_id)
            if category:
                stmt = stmt.where(ProductModel.category_code == category)
            stmt = stmt.order_by(ProductModel.id.desc()).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()
            return [product_model_to_dto(m) for m in rows]

    async def create(self, **kwargs: Any) -> Product:
        async with self.db.session() as session:
            schedule = kwargs.pop("schedule", None)
            model = ProductModel(
                place_id=kwargs["place_id"],
                name=kwargs["name"],
                description=kwargs.get("description") or "",
                price=kwargs.get("price"),
                category_code=kwargs["category_code"],
                schedule=schedule_to_json(schedule) if schedule is not None else None,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return product_model_to_dto(model)

    async def update(self, product_id: int, **kwargs: Any) -> Optional[Product]:
        async with self.db.session() as session:
            model = await session.get(ProductModel, product_id)
            if model is None or model.deleted:
                return None
            for key, value in kwargs.items():
                if key == "schedule":
                    model.schedule = schedule_to_json(value)
                elif hasattr(model, key):
                    setattr(model, key, value)
            await session.commit()
            await session.refresh(model)
            return product_model_to_dto(model)

    async def soft_delete(self, product_id: int) -> bool:
        async with self.db.session() as session:
            model = await session.get(ProductModel, product_id)
            if model is None or model.deleted:
                return False
            model.deleted = True
            await session.commit()
            return True
