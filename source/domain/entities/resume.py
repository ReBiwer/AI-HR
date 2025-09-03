from datetime import datetime
from pydantic import EmailStr

from source.domain.entities.base import BaseEntity


class ExperienceEntity(BaseEntity):
    company: str
    position: str
    start_work: datetime
    end_work: datetime | None
    responsibilities: str
    achievements: str


class ContactEntity(BaseEntity):
    phone: str
    email: EmailStr
    telegram: str


class ResumeEntity(BaseEntity):
    name: str
    surname: str
    job_description: list[ExperienceEntity]
    skills: list[str]
    about_me: str
    contacts: ContactEntity
