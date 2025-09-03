from source.domain.entities.base import BaseEntity


class ResponseToVacancyEntity(BaseEntity):
    url_vacancy: str
    text: str
    quality: bool | None = None
