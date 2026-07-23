"""Репозиторий пользователей: наружу отдаём только DTO, не ORM."""

from typing import Optional, Protocol

from datetime import date

from sqlalchemy import select
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.libs.entities.place import PlaceCategory
from python.libs.entities.user import Status, User, UserRole
from python.user_service.src.user_service.infra.orm.mappers import user_model_to_dto
from python.user_service.src.user_service.infra.orm.models import UserModel


class UserRepo(Protocol):
    """Контракт репозитория пользователей."""

    async def get_by_id(self, user_id: int) -> Optional[User]:
        ...

    async def create(
        self,
        *,
        name: str,
        age: Optional[int] = None,
        short_bio: str = "",
        favorite_categories: list[PlaceCategory] | None = None,
        avatar_url: Optional[str] = None,
        city_id: Optional[int] = None,
        birthdate: Optional[date] = None,
        auth_account_id: Optional[int] = None,
    ) -> User:
        ...

    async def update_bio(self, user_id: int, long_bio: str) -> Optional[User]:
        ...

    async def complete_onboarding(self, user_id: int) -> Optional[User]:
        ...

    async def save(self, user: User) -> User:
        ...

    async def soft_delete(self, user_id: int) -> bool:
        ...


@bean
class UserRepoImpl(UserRepo):
    """SQLAlchemy-реализация. Все методы async, результат — DTO User."""

    db: Database

    async def get_by_id(self, user_id: int) -> Optional[User]:
        async with self.db.session() as session:
            model = await session.get(UserModel, user_id)
            if model is None or model.deleted:
                return None
            return user_model_to_dto(model)

    async def create(
        self,
        *,
        name: str,
        age: Optional[int] = None,
        short_bio: str = "",
        favorite_categories: list[PlaceCategory] | None = None,
        avatar_url: Optional[str] = None,
        city_id: Optional[int] = None,
        birthdate: Optional[date] = None,
        auth_account_id: Optional[int] = None,
    ) -> User:
        categories = [c.value for c in (favorite_categories or [])]
        model = UserModel(
            name=name,
            age=age,
            short_bio=short_bio or "",
            long_bio="",
            avatar_url=avatar_url,
            city_id=city_id,
            birthdate=birthdate,
            auth_account_id=auth_account_id,
            status=Status.ACTIVE.name,
            role=UserRole.REGULAR.name,
            favorite_categories=categories,
            onboarding_completed=False,
            deleted=False,
        )
        async with self.db.session() as session:
            session.add(model)
            await session.flush()
            await session.refresh(model)
            return user_model_to_dto(model)

    async def update_bio(self, user_id: int, long_bio: str) -> Optional[User]:
        async with self.db.session() as session:
            model = await session.get(UserModel, user_id)
            if model is None or model.deleted:
                return None
            model.long_bio = long_bio
            await session.flush()
            await session.refresh(model)
            return user_model_to_dto(model)

    async def complete_onboarding(self, user_id: int) -> Optional[User]:
        async with self.db.session() as session:
            model = await session.get(UserModel, user_id)
            if model is None or model.deleted:
                return None
            model.onboarding_completed = True
            await session.flush()
            await session.refresh(model)
            return user_model_to_dto(model)

    async def save(self, user: User) -> User:
        async with self.db.session() as session:
            model = await session.get(UserModel, user.id)
            if model is None:
                raise ValueError(f"Пользователь id={user.id} не найден")
            model.name = user.name
            model.age = user.age
            model.short_bio = user.short_bio
            model.long_bio = user.long_bio
            model.avatar_url = user.avatar_url
            model.status = user.status.name
            model.role = user.role.name
            model.favorite_categories = [c.value for c in user.favorite_categories]
            model.onboarding_completed = user.onboarding_completed
            model.deleted = user.deleted
            await session.flush()
            await session.refresh(model)
            return user_model_to_dto(model)

    async def list_active(self, limit: int = 50, offset: int = 0) -> list[User]:
        async with self.db.session() as session:
            stmt = (
                select(UserModel)
                .where(UserModel.deleted.is_(False))
                .order_by(UserModel.id)
                .limit(limit)
                .offset(offset)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [user_model_to_dto(m) for m in rows]

    async def soft_delete(self, user_id: int) -> bool:
        async with self.db.session() as session:
            model = await session.get(UserModel, user_id)
            if model is None or model.deleted:
                return False
            model.deleted = True
            await session.flush()
            return True
