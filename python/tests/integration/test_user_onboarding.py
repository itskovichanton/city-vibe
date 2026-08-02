"""Integration tests (testcontainers: Postgres) — профиль, онбординг, Милана."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON_ROOT = Path(__file__).resolve().parents[2]
USER_SRC = PYTHON_ROOT / "user_service" / "src"
SITE = Path("/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages")

for p in (REPO_ROOT, USER_SRC, SITE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from python.libs.clients.db import Database  # noqa: E402
from python.libs.entities.place import PlaceCategory  # noqa: E402
from python.libs.entities.user import Gender, UserRole  # noqa: E402
from python.user_service.src.user_service.entities.common import (  # noqa: E402
    CompleteOnboardingRequest,
    UpdateBioRequest,
    UpdateProfileRequest,
)
from python.user_service.src.user_service.repo.user import UserRepoImpl  # noqa: E402
from python.user_service.src.user_service.usecase.complete_onboarding import (  # noqa: E402
    CompleteOnboardingUseCaseImpl,
)
from python.user_service.src.user_service.usecase.get_milana_account import (  # noqa: E402
    GetMilanaAccountUseCaseImpl,
)
from python.user_service.src.user_service.usecase.update_bio import UpdateBioUseCaseImpl  # noqa: E402
from python.user_service.src.user_service.usecase.update_profile import (  # noqa: E402
    UpdateProfileUseCaseImpl,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
]


def _docker_available() -> bool:
    try:
        import docker

        docker.from_env().ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def postgres_container():
    if not _docker_available():
        pytest.skip("Docker недоступен — integration tests пропущены")
    from testcontainers.postgres import PostgresContainer

    pg = PostgresContainer("postgres:16-alpine")
    try:
        pg.start()
        yield {
            "pg_url": pg.get_connection_url().replace("psycopg2", "asyncpg"),
            "pg_sync_url": pg.get_connection_url(),
        }
    except Exception as exc:
        pytest.skip(f"Testcontainers недоступны: {exc}")
    finally:
        try:
            pg.stop()
        except Exception:
            pass


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def user_stack(postgres_container):
    migrations_dir = PYTHON_ROOT / "user_service" / "sql" / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))

    import psycopg2

    sync_url = postgres_container["pg_sync_url"].replace(
        "postgresql+psycopg2://",
        "postgresql://",
    )
    conn = psycopg2.connect(sync_url)
    conn.autocommit = True
    cur = conn.cursor()
    for sql_file in sql_files:
        cur.execute(sql_file.read_text(encoding="utf-8"))
    cur.close()
    conn.close()

    db = object.__new__(Database)
    db.url = postgres_container["pg_url"]
    db.echo = False
    db.pool_size = 3
    db.init()

    from sqlalchemy import text

    async with db.engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

    repo = object.__new__(UserRepoImpl)
    repo.db = db

    outbox = AsyncMock()

    update_profile_uc = object.__new__(UpdateProfileUseCaseImpl)
    update_profile_uc.user_repo = repo
    update_profile_uc.outbox = outbox

    update_bio_uc = object.__new__(UpdateBioUseCaseImpl)
    update_bio_uc.user_repo = repo
    update_bio_uc.outbox = outbox

    complete_uc = object.__new__(CompleteOnboardingUseCaseImpl)
    complete_uc.user_repo = repo
    complete_uc.outbox = outbox

    get_milana_uc = object.__new__(GetMilanaAccountUseCaseImpl)
    get_milana_uc.user_repo = repo

    try:
        yield {
            "repo": repo,
            "update_profile_uc": update_profile_uc,
            "update_bio_uc": update_bio_uc,
            "complete_uc": complete_uc,
            "get_milana_uc": get_milana_uc,
        }
    finally:
        await db.engine.dispose()


async def test_update_profile_name_and_categories(user_stack):
    repo = user_stack["repo"]
    uc = user_stack["update_profile_uc"]

    created = await repo.create(
        name="Иван",
        gender=Gender.MALE,
        favorite_categories=[],
    )

    updated = await uc.execute(
        UpdateProfileRequest(
            user_id=created.id,
            name="Алексей",
            favorite_categories=[
                PlaceCategory.BARS,
                PlaceCategory.THEATERS,
            ],
        )
    )

    assert updated.name == "Алексей"
    assert PlaceCategory.BARS in updated.favorite_categories
    assert PlaceCategory.THEATERS in updated.favorite_categories

    stored = await repo.get_by_id(created.id)
    assert stored is not None
    assert stored.name == "Алексей"
    assert PlaceCategory.BARS in stored.favorite_categories


async def test_get_milana_service_account(user_stack):
    milana = await user_stack["get_milana_uc"].execute()
    assert milana.name == "Милана"
    assert milana.role == UserRole.MILANA
    assert milana.onboarding_completed is True


async def test_onboarding_flow_profile_bio_complete(user_stack):
    repo = user_stack["repo"]
    user = await repo.create(name="Онбординг", gender=Gender.FEMALE)

    step1 = await user_stack["update_profile_uc"].execute(
        UpdateProfileRequest(
            user_id=user.id,
            name="Мария",
            favorite_categories=[PlaceCategory.CAFES, PlaceCategory.PARKS],
        )
    )
    assert step1.name == "Мария"
    assert step1.onboarding_completed is False

    step2 = await user_stack["update_bio_uc"].execute(
        UpdateBioRequest(
            user_id=user.id,
            long_bio="Обожаю атмосферные места и парки.",
        )
    )
    assert "атмосферные" in step2.long_bio

    done = await user_stack["complete_uc"].execute(
        CompleteOnboardingRequest(user_id=user.id),
    )
    assert done.onboarding_completed is True
    assert PlaceCategory.CAFES in done.favorite_categories
    assert PlaceCategory.PARKS in done.favorite_categories
