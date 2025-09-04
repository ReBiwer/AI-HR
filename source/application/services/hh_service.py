from typing import TypedDict
from abc import ABC, abstractmethod

from source.domain.entities.resume import ResumeEntity
from source.domain.entities.response import ResponseToVacancyEntity


class AuthTokens(TypedDict):
    access_token: str
    refresh_token: str


class IHHService(ABC):

    @abstractmethod
    async def auth(self) -> AuthTokens:
        """Метод для авторизации, возвращает словарь с access и refresh токенами"""
        ...

    @abstractmethod
    async def get_resume(self, resume_id: str) -> ResumeEntity:
        """Метод для загрузки резюме"""
        ...

    @abstractmethod
    async def get_resumes(self) -> list[ResumeEntity]:
        """Метод для получения всех имеющихся резюме"""
        ...

    @abstractmethod
    async def send_response_to_vacancy(self, response: ResponseToVacancyEntity) -> None:
        """Метод для отправки отклика на вакансию"""
        ...
