from datetime import datetime
from pydantic import EmailStr, BaseModel

from source.domain.entities.base import BaseEntity


class ExperienceEntity(BaseModel):
    company: str
    position: str
    start: datetime
    end: datetime | None
    description: str


class ContactEntity(BaseModel):
    phone: str
    email: EmailStr


class ResumeEntity(BaseEntity):
    name: str
    surname: str
    job_description: list[ExperienceEntity]
    skills: set[str]
    contacts: ContactEntity
