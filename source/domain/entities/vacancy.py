from typing import TypedDict, Union

from source.domain.entities.base import BaseEntity


class Experience(TypedDict):
    id: Union[str, int]
    name: str


class VacancyEntity(BaseEntity):
    url_vacancy: str
    name: str
    experience: Experience
    description: str
    key_skills: list[dict[str, str]]
    employer_id: str
