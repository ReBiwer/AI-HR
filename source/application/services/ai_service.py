from typing import TypedDict
from abc import ABC, abstractmethod

from source.domain.entities.response import ResponseToVacancyEntity
from source.domain.entities.query import QueryEntity
from source.domain.entities.resume import ResumeEntity
from source.domain.entities.vacancy import VacancyEntity
from source.domain.entities.employer import EmployerEntity


class GenerateResponseData(TypedDict):
    vacancy: VacancyEntity
    resume: ResumeEntity
    query: QueryEntity
    employer: EmployerEntity
    good_responses: list[ResponseToVacancyEntity]
    user_rules: dict


class IAIService(ABC):

    @abstractmethod
    async def generate_response(
            self,
            data: GenerateResponseData
    ) -> ResponseToVacancyEntity:
        """Метод для генерации отклика на вакансию"""
        ...
