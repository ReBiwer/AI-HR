from typing import AsyncGenerator

import pytest
from alembic import config, command
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from source.infrastructure.db.repositories.user import UserRepository
from source.infrastructure.db.repositories.resume import (
    JobExperienceRepository,
    ResumeRepository,
)
from source.infrastructure.settings.test import TestAppSettings


@pytest.fixture(scope="package")
def async_engine(test_settings: TestAppSettings) -> AsyncEngine:
    return create_async_engine(test_settings.db_url)


@pytest.fixture(scope="package")
def async_session_maker(async_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )


@pytest.fixture(scope="package", autouse=True)
async def run_migration(
    request, test_settings: TestAppSettings, async_engine: AsyncEngine
) -> None:
    if not request.config.getoption("--run-migrations"):
        return
    alembic_config = config.Config(f"{test_settings.BASE_DIR}/alembic.ini")
    async with async_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: (
                alembic_config.attributes.__setitem__("connection", sync_conn),
                command.upgrade(alembic_config, "head"),
            )
        )


@pytest.fixture()
async def async_session(
    async_session_maker: async_sessionmaker[AsyncSession], async_engine: AsyncEngine
) -> AsyncGenerator[AsyncSession, None]:
    async with async_engine.connect() as conn:
        root_tx = await conn.begin()
        try:
            async with async_session_maker(bind=conn) as sess:
                yield sess
        finally:
            await root_tx.rollback()
            await conn.close()


@pytest.fixture()
def user_repo(async_session: AsyncSession) -> UserRepository:
    return UserRepository(async_session)


@pytest.fixture()
def resume_repository(async_session: AsyncSession) -> ResumeRepository:
    return ResumeRepository(async_session)


@pytest.fixture()
def job_experience_repository(async_session: AsyncSession) -> JobExperienceRepository:
    return JobExperienceRepository(async_session)
