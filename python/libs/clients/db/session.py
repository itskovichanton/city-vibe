"""Подключение к PostgreSQL через SQLAlchemy (async)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.mybootstrap_ioc_itskovichanton.ioc import bean


@bean(
    url=(
        "db.url",
        str,
        "postgresql+asyncpg://cityvibe:cityvibe@localhost:5432/cityvibe_users",
    ),
    echo=("db.echo", bool, False),
    pool_size=("db.pool_size", int, 5),
)
class Database:
    """
    Обёртка над async SQLAlchemy engine / session factory.

    url берётся из config.yml (секция db.url), например:
      postgresql+asyncpg://user:pass@localhost:5432/cityvibe_users
    """

    engine: AsyncEngine | None = None
    session_factory: async_sessionmaker[AsyncSession] | None = None

    def init(self, **kwargs):
        self.url = kwargs.get("url", getattr(self, "url", None))
        self.echo = kwargs.get("echo", getattr(self, "echo", False))
        self.pool_size = kwargs.get("pool_size", getattr(self, "pool_size", 5))

        self.engine = create_async_engine(
            self.url,
            echo=self.echo,
            pool_size=self.pool_size,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        # SQL-спаны в Jaeger (если CITYVIBE_TRACING_ENABLED)
        try:
            from python.libs.infra.tracing import instrument_sqlalchemy

            instrument_sqlalchemy(self.engine)
        except Exception:
            pass

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Контекстный менеджер сессии: commit при успехе, rollback при ошибке."""
        assert self.session_factory is not None, "Database не инициализирован"
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def dispose(self) -> None:
        """Закрытие пула соединений."""
        if self.engine is not None:
            await self.engine.dispose()
