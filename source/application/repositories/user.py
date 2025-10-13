from abc import ABC

from source.application.repositories.base import ISQLRepository
from source.domain.entities.user import UserEntity


class IUserRepository[ET: UserEntity](ISQLRepository[UserEntity], ABC): ...
