from sqlalchemy import select

from source.infrastructure.db.models.base import BaseModel
from source.application.repositories.base import ISQLRepository
from source.domain.entities.base import BaseEntity


class SQLAlchemyRepository[ET: BaseEntity, DBModel: BaseModel](ISQLRepository[ET]):
    model_class: type[DBModel]
    entity_class: type[ET]

    def _validate_entity_to_db_model(self, data: ET) -> DBModel:
        raise NotImplementedError

    async def _check_exist_entity(self, data: ET) -> DBModel | None:
        raise NotImplementedError

    async def get(self, **filters) -> ET | None:
        stmt = select(self.model_class).filter_by(**filters)
        result = await self.session.execute(stmt)
        model_instance = result.scalar_one_or_none()
        if model_instance:
            return self.entity_class.model_validate(model_instance.dump_dict())
        return None

    async def create(self, entity: ET) -> ET:
        existing_instance = await self._check_exist_entity(entity)
        if existing_instance:
            return self.entity_class.model_validate(existing_instance.dump_dict())

        model_instance = self._validate_entity_to_db_model(entity)
        self.session.add(model_instance)
        await self.session.flush()
        return self.entity_class.model_validate(model_instance.dump_dict())

    async def update(self, entity: ET) -> ET:
        if entity.id is None:
            msg = f"Невозможно обновить {self.entity_class.__name__} без идентификатора"
            raise ValueError(msg)

        model_instance = await self.session.get(self.model_class, entity.id)
        update_data = entity.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if not isinstance(key, BaseModel.__class__) and not isinstance(value, list):
                setattr(model_instance, key, value)

        await self.session.flush()
        return self.entity_class.model_validate(model_instance.dump_dict())

    async def delete(self, id_entity: int) -> None:
        model_instance = await self.session.get(self.model_class, id_entity)
        if model_instance:
            await self.session.delete(model_instance)
