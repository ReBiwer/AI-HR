from source.infrastructure.db.repositories.user import UserRepository
from source.domain.entities.user import UserEntity


async def test_create_user(user_repo: UserRepository, test_user_entity: UserEntity):
    result = await user_repo.create(test_user_entity)
    assert result
    assert isinstance(result, UserEntity)


async def test_get_user(user_repo: UserRepository, test_user_entity: UserEntity):
    new_user = await user_repo.create(test_user_entity)
    result = await user_repo.get(new_user.id)
    assert result
    assert isinstance(result, UserEntity)


async def test_update_user(user_repo: UserRepository, test_user_entity: UserEntity):
    new_user = await user_repo.create(test_user_entity)
    test_user_entity.id = new_user.id
    test_user_entity.name = "Vladimir"
    updated_user: UserEntity = await user_repo.update(test_user_entity)
    assert updated_user
    assert updated_user.name == "Vladimir"
    assert new_user != updated_user


async def test_delete_user(user_repo: UserRepository, test_user_entity: UserEntity):
    await user_repo.delete(test_user_entity.id)
    check = await user_repo.get(test_user_entity.id)
    assert check is None
