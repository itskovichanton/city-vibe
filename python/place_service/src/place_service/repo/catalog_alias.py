"""Репозиторий синонимов catalog_aliases."""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.place_service.src.place_service.infra.catalog_match import CatalogAlias
from python.place_service.src.place_service.infra.orm.models import CatalogAliasModel


class CatalogAliasRepo(Protocol):
    async def list_by_catalog(self, catalog: str) -> list[CatalogAlias]: ...


@bean
class CatalogAliasRepoImpl(CatalogAliasRepo):
    db: Database

    async def list_by_catalog(self, catalog: str) -> list[CatalogAlias]:
        async with self.db.session() as session:
            stmt = select(CatalogAliasModel).where(
                CatalogAliasModel.catalog == catalog,
                CatalogAliasModel.deleted.is_(False),
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [
                CatalogAlias(
                    catalog=m.catalog,
                    target_code=m.target_code,
                    alias=m.alias,
                    why=m.why or "",
                    weight=float(m.weight or 1.0),
                )
                for m in rows
            ]
