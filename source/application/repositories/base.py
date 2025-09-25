from abc import ABC, abstractmethod
from typing import Protocol

from source.domain.entities.base import BaseEntity


class IRepository[ET: BaseEntity](ABC):
    @abstractmethod
    async def get(self, id_entity: int) -> ET | None: ...

    @abstractmethod
    async def create(self, entity: ET) -> ET: ...

    @abstractmethod
    async def update(self, entity: ET) -> ET: ...

    @abstractmethod
    async def delete(self, id_entity: int) -> None: ...


class IUnitOfWork(Protocol):
    async def __aenter__(self): ...

    async def __aexit__(self, exc_type, exc_val, exc_tb): ...
