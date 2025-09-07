from typing import TypedDict

from source.domain.entities.base import BaseEntity


class Experience(TypedDict):
    id: str
    name: str


class VacancyEntity(BaseEntity):
    name: str
    experience: Experience
    description: str
    key_skills: set[str]
