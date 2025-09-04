from source.domain.entities.base import BaseEntity


class ResponseToVacancyEntity(BaseEntity):
    url_vacancy: str
    vacancy_id: str
    resume_id: str
    message: str
    quality: bool | None = None
