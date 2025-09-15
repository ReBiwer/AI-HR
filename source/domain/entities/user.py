from pydantic import EmailStr

from source.domain.entities.resume import ResumeEntity
from source.domain.entities.base import BaseEntity


class UserEntity(BaseEntity):
    name: str
    mid_name: str | None = None
    last_name: str
    phone: str
    email: EmailStr | None = None
    resume: ResumeEntity | None = None
