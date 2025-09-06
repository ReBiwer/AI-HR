from typing import TypedDict

from source.domain.entities.base import BaseEntity


class QueryEntity(BaseEntity):
    url_vacancy: str
    vacancy_id: str


class Experience(TypedDict):
    id: str
    name: str


class VacancyEntity(BaseEntity):
    name: str
    experience: Experience
    description: str
    key_skills: set[str]
