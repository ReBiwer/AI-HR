import re
import asyncio
from typing import TypedDict
from abc import ABC, abstractmethod

from source.application.services.ai_service import GenerateResponseData
from source.domain.entities.vacancy import VacancyEntity
from source.domain.entities.employer import EmployerEntity
from source.domain.entities.resume import ResumeEntity
from source.domain.entities.response import ResponseToVacancyEntity
from source.domain.entities.user import UserEntity


class AuthTokens(TypedDict):
    access_token: str
    refresh_token: str


class IHHService(ABC):

    @staticmethod
    def extract_vacancy_id_from_url(url: str) -> str:
        pattern = r"/https?:\/\/[^\/]+\.hh\.ru\/vacancy\/(\d+)/gm"
        match = re.search(pattern, url)
        return match.group(1)

    @abstractmethod
    async def get_me(self) -> UserEntity:
        """Метод возвращает информацию о залогиненным пользователе"""
        ...

    @abstractmethod
    def get_auth_url(self, state: str) -> str:
        """Метод для получения url для OAuth авторизации"""
        ...

    @abstractmethod
    async def auth(self, code: str) -> AuthTokens:
        """Метод для авторизации, принимает код полученный после редиректа
         возвращает словарь с access и refresh токенами"""
        ...

    @abstractmethod
    async def get_vacancy_data(self, vacancy_id: str) -> VacancyEntity:
        """Метод для получения информации о вакансии"""
        ...

    @abstractmethod
    async def get_employer_data(self, employer_id: str) -> EmployerEntity:
        """Метод для получения информации о работодателе"""
        ...

    @abstractmethod
    async def get_resume_data(self, resume_id: str) -> ResumeEntity:
        """Метод для получения информации из резюме авторизованного пользователя"""
        ...

    @abstractmethod
    async def get_good_responses(self, quantity_responses: int = 10) -> list[ResponseToVacancyEntity]:
        """Метод для получения определенного количества удачных откликов"""
        ...

    @abstractmethod
    async def get_user_rules(self) -> dict:
        """Метод для получения правил пользователя для формирования отклика"""
        ...

    @abstractmethod
    async def data_collect_for_llm(
            self,
            vacancy_id: str,
            resume_id: str,
    ) -> GenerateResponseData:
        """Метод для сбора всех данных для отправки в llm для генерации отклика"""
        ...

    @abstractmethod
    async def send_response_to_vacancy(self, response: ResponseToVacancyEntity) -> bool:
        """Метод для отправки отклика на вакансию"""
        ...
