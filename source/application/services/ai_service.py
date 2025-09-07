from abc import ABC, abstractmethod

from source.domain.entities.response import ResponseToVacancyEntity
from source.domain.entities.base import BaseEntity


class IAIService(ABC):

    @abstractmethod
    async def generate_response(
            self,
            data: dict[str, BaseEntity]
    ) -> ResponseToVacancyEntity:
        """Метод для генерации отклика на вакансию"""
        ...
