from source.infrastructure.db.repositories.base import SQLAlchemyRepository
from source.infrastructure.db.models.user import UserModel
from source.domain.entities.user import UserEntity


class UserRepository[ET: UserEntity, DBModel: UserModel](SQLAlchemyRepository):
    model_class = UserModel
    entity_class = UserEntity
