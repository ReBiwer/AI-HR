from abc import ABC

from source.application.repositories.base import IRepository
from source.domain.entities.user import UserEntity


class IUserRepository[ET: UserEntity](IRepository[UserEntity], ABC):
    ...
