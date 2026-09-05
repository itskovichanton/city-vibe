"""Репозиторий категорий товаров и услуг."""

from __future__ import annotations

from typing import Optional, Protocol

from sqlalchemy import select
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.libs.entities.place import ProductCategoryInfo
from python.place_service.src.place_service.infra.orm.mappers import product_category_model_to_dto
from python.place_service.src.place_service.infra.orm.models import ProductCategoryModel


class ProductCategoryRepo(Protocol):
    async def list_active(self) -> list[ProductCategoryInfo]: ...

    async def get_by_code(self, code: str) -> Optional[ProductCategoryInfo]: ...


@bean
class ProductCategoryRepoImpl(ProductCategoryRepo):
    db: Database

    async def list_active(self) -> list[ProductCategoryInfo]:
        async with self.db.session() as session:
            stmt = (
                select(ProductCategoryModel)
                .where(
                    ProductCategoryModel.deleted.is_(False),
                    ProductCategoryModel.is_active.is_(True),
                )
                .order_by(ProductCategoryModel.sort_order, ProductCategoryModel.title)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [product_category_model_to_dto(m) for m in rows]

    async def get_by_code(self, code: str) -> Optional[ProductCategoryInfo]:
        async with self.db.session() as session:
            stmt = select(ProductCategoryModel).where(
                ProductCategoryModel.code == code,
                ProductCategoryModel.deleted.is_(False),
            )
            model = (await session.execute(stmt)).scalar_one_or_none()
            return product_category_model_to_dto(model) if model else None
