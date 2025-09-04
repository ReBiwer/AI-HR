from abc import ABC, abstractmethod

from source.domain.entities.resume import ResumeEntity
from source.domain.entities.query import QueryEntity
from source.domain.entities.response import ResponseToVacancyEntity


class IAIService(ABC):

    @abstractmethod
    async def generate_response(
            self,
            query: QueryEntity,
            resume: ResumeEntity
    ) -> ResponseToVacancyEntity:
        """Метод для генерации отклика на вакансию"""
        ...
