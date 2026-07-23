from __future__ import annotations

from typing import Optional, Protocol

from sqlalchemy import select
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.design_service.src.design_service.infra.orm.mappers import pin_model_to_dto
from python.design_service.src.design_service.infra.orm.models import MapPinStyleModel
from python.libs.clients.db import Database
from python.libs.entities.design import MapPinStyle


class PinStyleRepo(Protocol):
    async def list_all(self) -> list[MapPinStyle]: ...

    async def get_by_id(self, style_id: int) -> Optional[MapPinStyle]: ...

    async def get_by_code(self, code: str) -> Optional[MapPinStyle]: ...


@bean
class PinStyleRepoImpl(PinStyleRepo):
    db: Database

    async def list_all(self) -> list[MapPinStyle]:
        async with self.db.session() as session:
            stmt = (
                select(MapPinStyleModel)
                .where(MapPinStyleModel.deleted.is_(False))
                .order_by(MapPinStyleModel.id)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [pin_model_to_dto(m) for m in rows]

    async def get_by_id(self, style_id: int) -> Optional[MapPinStyle]:
        async with self.db.session() as session:
            model = await session.get(MapPinStyleModel, style_id)
            if model is None or model.deleted:
                return None
            return pin_model_to_dto(model)

    async def get_by_code(self, code: str) -> Optional[MapPinStyle]:
        async with self.db.session() as session:
            stmt = select(MapPinStyleModel).where(
                MapPinStyleModel.code == code, MapPinStyleModel.deleted.is_(False)
            )
            model = (await session.execute(stmt)).scalar_one_or_none()
            return pin_model_to_dto(model) if model else None
