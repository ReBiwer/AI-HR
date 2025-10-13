import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from source.infrastructure.db.uow import UnitOfWork
from source.infrastructure.db.repositories.user import UserRepository
from source.domain.entities.user import UserEntity


async def test_uow_commit(async_session: AsyncSession, test_user_entity: UserEntity):
    async with UnitOfWork(async_session) as session:
        user_repo = UserRepository(session)
        created = await user_repo.create(test_user_entity)
        assert created.id is not None

    # после выхода должно быть commit, сущность доступна для чтения
    fetched = await user_repo.get(created.id)
    assert fetched is not None
    assert fetched.name == test_user_entity.name


async def test_uow_rollback_on_exception(
    async_session: AsyncSession, test_user_entity: UserEntity
):
    class Boom(Exception):
        pass

    with pytest.raises(Boom):
        async with UnitOfWork(async_session) as session:
            user_repo = UserRepository(session)
            await user_repo.create(test_user_entity)
            raise Boom()

    # после исключения – откат, сущности не должно быть
    result = await user_repo.get(test_user_entity.id)
    assert result is None
