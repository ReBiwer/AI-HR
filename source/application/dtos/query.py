from source.application.dtos.base import BaseDTO


class QueryCreateDTO(BaseDTO):
    url_vacancy: str
    resume_id: str
