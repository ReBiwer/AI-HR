from source.application.services.ai_service import IAIService
from source.application.services.hh_service import IHHService
from source.application.dtos.query import QueryCreateDTO
from source.domain.entities.query import QueryEntity
from source.domain.entities.response import ResponseToVacancyEntity


class GenerateResponseUseCase:

    def __init__(self, hh_service: IHHService, ai_service: IAIService):
        self.hh_service = hh_service
        self.ai_service = ai_service

    async def __call__(self, query: QueryCreateDTO) -> ResponseToVacancyEntity:
        resume = await self.hh_service.get_resume_data(query.resume_id)
        query_entity = QueryEntity.model_validate(query, from_attributes=True)
        response = await self.ai_service.generate_response(query_entity, resume)
        return response
