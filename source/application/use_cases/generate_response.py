from source.application.services.ai_service import IAIService
from source.application.services.hh_service import IHHService
from source.application.dtos.query import QueryCreateDTO
from source.domain.entities.response import ResponseToVacancyEntity


class GenerateResponseUseCase:

    def __init__(self, hh_service: IHHService, ai_service: IAIService):
        self.hh_service = hh_service
        self.ai_service = ai_service

    async def __call__(self, query: QueryCreateDTO) -> ResponseToVacancyEntity:
        vacancy_id = self.hh_service.extract_vacancy_id_from_url(query.url_vacancy)
        data = await self.hh_service.data_collect_for_llm(query.user_id, vacancy_id, query.resume_id)
        response = await self.ai_service.generate_response(data)
        return response
