from pydantic import Field

from source.application.dtos.base import BaseDTO


class QueryCreateDTO(BaseDTO):
    url_vacancy: str = Field(default="https://usinsk.hh.ru/vacancy/125537679")
    resume_id: str = Field(default="6044a353ff0f1126620039ed1f42324e494b4c")
