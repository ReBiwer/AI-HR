from source.application.services.ai_service import IAIService
from source.application.services.hh_service import IHHService
from source.application.dtos.query import QueryRecreateDTO
from source.domain.entities.response import ResponseToVacancyEntity


class RegenerateResponseUseCase:
    def __init__(self, hh_service: IHHService, ai_service: IAIService):
        self.hh_service = hh_service
        self.ai_service = ai_service

    async def __call__(self, query: QueryRecreateDTO) -> ResponseToVacancyEntity:
        try:
            new_response = await self.ai_service.regenerate_response(
                query.user_id, query.response, query.user_comments
            )
            return new_response
        except ValueError:
            vacancy_id = self.hh_service.extract_vacancy_id_from_url(query.url_vacancy)
            data = await self.hh_service.data_collect_for_llm(
                query.subject,
                query.user_id,
                vacancy_id,
                query.resume_id,
            )
            new_response = await self.ai_service.regenerate_response(
                query.user_id, query.response, query.user_comments, data=data
            )
            return new_response
