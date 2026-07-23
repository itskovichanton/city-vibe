from __future__ import annotations

from typing import Optional, Protocol

from sqlalchemy import select
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.design_service.src.design_service.infra.orm.mappers import theme_model_to_dto
from python.design_service.src.design_service.infra.orm.models import ChatThemeModel
from python.libs.clients.db import Database
from python.libs.entities.design import ChatTheme


class ChatThemeRepo(Protocol):
    async def list_all(self) -> list[ChatTheme]: ...

    async def get_by_id(self, theme_id: int) -> Optional[ChatTheme]: ...

    async def get_by_code(self, code: str) -> Optional[ChatTheme]: ...


@bean
class ChatThemeRepoImpl(ChatThemeRepo):
    db: Database

    async def list_all(self) -> list[ChatTheme]:
        async with self.db.session() as session:
            stmt = (
                select(ChatThemeModel)
                .where(ChatThemeModel.deleted.is_(False))
                .order_by(ChatThemeModel.id)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [theme_model_to_dto(m) for m in rows]

    async def get_by_id(self, theme_id: int) -> Optional[ChatTheme]:
        async with self.db.session() as session:
            model = await session.get(ChatThemeModel, theme_id)
            if model is None or model.deleted:
                return None
            return theme_model_to_dto(model)

    async def get_by_code(self, code: str) -> Optional[ChatTheme]:
        async with self.db.session() as session:
            stmt = select(ChatThemeModel).where(
                ChatThemeModel.code == code, ChatThemeModel.deleted.is_(False)
            )
            model = (await session.execute(stmt)).scalar_one_or_none()
            return theme_model_to_dto(model) if model else None
