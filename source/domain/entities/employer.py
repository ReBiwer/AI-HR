from source.domain.entities.base import BaseEntity


class EmployerEntity(BaseEntity):
    hh_id: str
    name: str
    description: str

    def __str__(self):
        return (
            f"Название компании: {self.name}\n" f"Описание компании: {self.description}"
        )
