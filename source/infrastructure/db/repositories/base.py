from abc import ABC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from source.infrastructure.db.models.base import BaseModel
from source.application.repositories.base import IRepository
from source.domain.entities.base import BaseEntity


class ISQLRepository[ET: BaseEntity](IRepository, ABC):
    def __init__(self, session: AsyncSession):
        self.session = session


class SQLAlchemyRepository[ET: BaseEntity, DBModel: BaseModel](ISQLRepository[ET]):
    model_class: type[DBModel]
    entity_class: type[ET]

    async def get(self, id_entity: int) -> ET | None:
        stmt = select(self.model_class).where(self.model_class.id == id_entity)
        result = await self.session.execute(stmt)
        model_instance = result.scalar_one_or_none()
        if model_instance:
            return self.entity_class.model_validate(model_instance)
        return None

    async def create(self, entity: ET) -> ET:
        model_instance = self.model_class(**entity.model_dump())
        self.session.add(model_instance)
        await self.session.flush()
        return self.entity_class.model_validate(model_instance)

    async def update(self, entity: ET) -> ET:
        model_instance = await self.session.get(self.model_class, entity.id)
        update_data = entity.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(model_instance, key, value)

        await self.session.flush()
        return self.entity_class.model_validate(model_instance)

    async def delete(self, id_entity: int) -> None:
        model_instance = await self.session.get(self.model_class, id_entity)
        if model_instance:
            await self.session.delete(model_instance)
