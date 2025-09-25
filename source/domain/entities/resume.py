from datetime import datetime
from pydantic import EmailStr, BaseModel

from source.domain.entities.base import BaseEntity


class JobExperienceEntity(BaseModel):
    company: str
    position: str
    start: datetime
    end: datetime | None
    description: str

    def __str__(self):
        return (
            f"Компания: {self.company}\n"
            f"Позиция: {self.position}\n"
            f"Начало работы: c {self.start} {f'по {self.end}\n' if self.end else '\n'}"
            f"Описание: {self.description}"
        )


class ResumeEntity(BaseEntity):
    hh_id: str
    name: str
    surname: str
    job_experience: list[JobExperienceEntity]
    skills: set[str]
    contact_phone: str
    contact_email: EmailStr

    def __str__(self):
        job_experience = "\n".join(
            [str(experience) for experience in self.job_experience]
        )
        return (
            f"Имя: {self.name}, фамилия: {self.surname}\n"
            f"Опыт работы: {job_experience}\n"
            f"Навыки: {', '.join(self.skills)}\n"
            f"Контакты: телефон {self.contact_phone}, email {self.contact_email}"
        )
