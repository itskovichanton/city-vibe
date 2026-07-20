"""ORM-модели SQLAlchemy. Не отдаём наружу — репозитории мапят в DTO."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс всех ORM-моделей user-service."""


class UserModel(Base):
    """Таблица пользователей."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    short_bio: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    long_bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Статус / роль храним строками — проще миграции и OpenAPI
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="REGULAR")
    # Массив кодов категорий (bars, cafes, ...)
    favorite_categories: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)),
        nullable=False,
        default=list,
        server_default="{}",
    )
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    city_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    birthdate: Mapped[date | None] = mapped_column(Date, nullable=True)
    auth_account_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    devices: Mapped[list["UserDeviceModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserDeviceModel(Base):
    """Устройства пользователя (push-токены)."""

    __tablename__ = "user_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_model: Mapped[str] = mapped_column(String(255), nullable=False)
    push_token: Mapped[str] = mapped_column(String(512), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    os_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[UserModel] = relationship(back_populates="devices")
