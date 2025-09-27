import asyncio
from typing import Optional, Dict, Any
from hh_api.auth.keyed_stores import InMemoryKeyedTokenStore
from hh_api.auth.token_manager import OAuthConfig
from hh_api.client import HHClient, TokenManager, Subject

from source.application.services.ai_service import GenerateResponseData
from source.domain.entities.employer import EmployerEntity
from source.domain.entities.user import UserEntity
from source.domain.entities.vacancy import Experience, VacancyEntity
from source.infrastructure.settings.app import app_settings
from source.application.services.hh_service import IHHService, AuthTokens
from source.domain.entities.response import ResponseToVacancyEntity
from source.domain.entities.resume import ResumeEntity, JobExperienceEntity


class MyHHClient(HHClient):
    async def get_employer(
        self, employer_id: str, *, subject: Optional[Subject] = None
    ) -> Dict[str, Any]:
        return (
            await self._request(
                "GET",
                f"/employers/{employer_id}",
                subject=subject,
            )
        ).json()

    async def get_me(self, subject: Optional[Subject] = None) -> Dict[str, Any]:
        return (
            await self._request(
                "GET",
                "/me",
                subject=subject,
            )
        ).json()

    async def get_resumes_from_url(
        self, url: str, subject: Optional[Subject] = None
    ) -> Dict[str, Any]:
        return (
            await self._request(
                "GET",
                url,
                subject=subject,
            )
        ).json()

    async def get_vacancies(
        self, subject: Optional[Subject], **filter_query
    ) -> Dict[str, Any]:
        return (
            await self._request(
                "GET", path="/vacancies", subject=subject, params=filter_query
            )
        ).json()


class HHService(IHHService):
    def __init__(self):
        self._oath_config = OAuthConfig(
            client_id=app_settings.HH_CLIENT_ID,
            client_secret=app_settings.HH_CLIENT_SECRET,
            redirect_uri=app_settings.HH_REDIRECT_URI,
            token_url="https://api.hh.ru/token",
        )
        self._user_agent = "AI HR/1.0 (bykov100898@yandex.ru)"
        self._keyed_store = InMemoryKeyedTokenStore()
        self._hh_tm = TokenManager(
            config=self._oath_config,
            store=self._keyed_store,
            user_agent=self._user_agent,
        )
        self.hh_client = MyHHClient(self._hh_tm)

    def _serialize_data_user(self, data: dict) -> UserEntity:
        """
        Сериализация данных пользователя возвращаемых из API hh.ru
        :param data: пример возвращаемых данных можно посмотреть тут: https://api.hh.ru/openapi/redoc#tag/Informaciya-o-soiskatele
        :return: UserEntity
        """
        user_data = {
            "id": data["id"],
            "name": data["first_name"],
            "mid_name": data["mid_name"],
            "last_name": data["last_name"],
            "phone": data["phone"],
            "email": data["email"] if data["email"] else None,
            "resumes": [
                self._serialize_data_resume(data) for data in data["resumes_data"]
            ],
        }
        return UserEntity.model_validate(user_data)

    @staticmethod
    def _serialize_data_vacancy(data: dict) -> VacancyEntity:
        """
        Сериализация данных возвращаемых из API hh.ru
        :param data: пример возвращаемых данных можно посмотреть тут: https://api.hh.ru/openapi/redoc#tag/Vakansii
        :return: VacancyEntity
        """
        vacancy_data = {
            "hh_id": data["id"],
            "url_vacancy": data["alternate_url"],
            "name": data["name"],
            "experience": Experience(
                id=data["experience"]["id"], name=data["experience"]["name"]
            ),
            "description": data["description"],
            "key_skills": data["key_skills"],
            "employer_id": data["employer"]["id"],
        }
        return VacancyEntity.model_validate(vacancy_data)

    @staticmethod
    def _serialize_data_employer(data: dict) -> EmployerEntity:
        """
        Сериализация данных возвращаемых из API hh.ru
        :param data: пример возвращаемых данных можно посмотреть тут: https://api.hh.ru/openapi/redoc#tag/Podskazki/operation/get-registered-companies-suggests
        :return: EmployerEntity
        """
        employer_data = {
            "hh_id": data["id"],
            "name": data["name"],
            "description": data["description"],
        }
        return EmployerEntity.model_validate(employer_data)

    @staticmethod
    def _serialize_data_resume(data: dict) -> ResumeEntity:
        """
        Сериализация данных возвращаемых из API hh.ru
        :param data: пример возвращаемых данных можно посмотреть тут: https://api.hh.ru/openapi/redoc#tag/Rezyume.-Prosmotr-informacii/operation/get-resume
        :return: ResumeEntity
        """
        resume_data = {
            "hh_id": data["id"],
            "title": data["title"],
            "name": data["first_name"],
            "surname": data["last_name"],
            "job_description": [
                JobExperienceEntity.model_validate(experience)
                for experience in data["experience"]
            ],
            "skills": data["skill_set"],
            "contact_phone": data["contact"]["phone"],
            "contact_email": data["contact"]["email"],
        }
        return ResumeEntity.model_validate(resume_data)

    @staticmethod
    def _serialize_data_response_to_vacancy(data: dict) -> ResponseToVacancyEntity:
        """
        Сериализация данных возвращаемых из API hh.ru
        :param data: пример возвращаемых данных можно посмотреть тут: https://api.hh.ru/openapi/redoc#tag/Perepiska-(otklikipriglasheniya)-dlya-soiskatelya/operation/get-negotiations
        :return:
        """
        response_data = {
            "hh_id": data["id"],
            "url_vacancy": data["url"],
            "vacancy_id": data["id"],
            "resume_id": data["resume"]["id"],
            # ключ-значение message было добавлено отдельно
            # схема получения находится тут
            # https://api.hh.ru/openapi/redoc#tag/Perepiska-(otklikipriglasheniya)-dlya-soiskatelya/operation/get-negotiation-messages
            "message": data["message"] if data["message"] else "",
            "quality": True,
        }
        return ResponseToVacancyEntity.model_validate(response_data)

    async def get_me(self, subject: Optional[Subject]) -> UserEntity:
        user_data = await self.hh_client.get_me(subject=subject)

        resumes_data = await self.hh_client.get_resumes_from_url(
            "/resumes/mine", subject=subject
        )
        # отдельный запрос делается, для подгрузки description
        # почему-то при загрузке всех резюме этого поля нет
        valid_resumes_data = await asyncio.gather(
            *[
                self.hh_client.get_resume(data["id"], subject=subject)
                for data in resumes_data["items"]
            ]
        )
        user_data["resumes_data"] = valid_resumes_data
        return self._serialize_data_user(user_data)

    def get_auth_url(self, state: str):
        return self._hh_tm.authorization_url(state)

    async def auth(self, code: str) -> AuthTokens:
        tokens = await self._hh_tm.exchange_code(
            app_settings.HH_FAKE_SUBJECT, code=code
        )
        return AuthTokens(
            access_token=tokens.access_token, refresh_token=tokens.refresh_token
        )

    async def get_vacancies(
        self, subject: Optional[Subject], **filter_query
    ) -> list[VacancyEntity]:
        vacancies = await self.hh_client.get_vacancies(subject, **filter_query)
        result = await asyncio.gather(
            *[self.get_vacancy_data(vacancy["id"]) for vacancy in vacancies["items"]]
        )
        return result

    async def get_vacancy_data(self, vacancy_id: str) -> VacancyEntity:
        data = await self.hh_client.get_vacancy(
            vacancy_id, subject=app_settings.HH_FAKE_SUBJECT
        )
        return self._serialize_data_vacancy(data)

    async def get_employer_data(self, employer_id: str) -> EmployerEntity:
        data = await self.hh_client.get_employer(
            employer_id, subject=app_settings.HH_FAKE_SUBJECT
        )
        return self._serialize_data_employer(data)

    async def get_resume_data(self, resume_id: str) -> ResumeEntity:
        data = await self.hh_client.get_resume(
            resume_id, subject=app_settings.HH_FAKE_SUBJECT
        )
        return self._serialize_data_resume(data)

    async def get_good_responses(
        self, quantity_responses: int = 10
    ) -> list[ResponseToVacancyEntity]:
        cur_page = 0
        invitations_responses = []
        # запрашиваем отклики у которых статус interview/собеседование
        while len(invitations_responses) != quantity_responses:
            try:
                coro_request = self.hh_client._request(
                    "GET",
                    "/negotiations",
                    # фильтрация по статус invitations/Активные приглашения не работает
                    # либо у меня нет таких откликов, либо нужно использовать другой статус (я его не нашел)
                    params={
                        "status": "active",
                        "per_page": quantity_responses,
                        "page": cur_page,
                    },
                    subject=app_settings.HH_FAKE_SUBJECT,
                )
                data = (await asyncio.wait_for(coro_request, timeout=100)).json()
                for item in data["items"]:
                    # в список добавляются только те отклики, у которых статус interview/собеседование
                    # и если список уже добавленных откликов не превышает переданный лимит
                    if (
                        item["state"]["id"] == "interview"
                        and len(invitations_responses) < quantity_responses
                    ):
                        invitations_responses.append(item)
                    # если длина собранных откликов уже соответствует, то останавливаем цикл
                    elif len(invitations_responses) == quantity_responses:
                        break
                cur_page += 1
            except asyncio.exceptions.TimeoutError:
                # если выходит исключение, то новых откликов больше нет
                break

        # создаем корутины для подгрузки сообщений откликов
        load_messages = [
            self.hh_client._request(
                "GET",
                f"/negotiations/{response['id']}/messages",
                subject=app_settings.HH_FAKE_SUBJECT,
            )
            for response in invitations_responses
        ]
        # конкурентно выполняем каждый запрос на подгрузку сообщений
        messages: list = await asyncio.gather(*load_messages)
        # добавляем отклик (первое сообщение в переписке) в список
        for response, mess in zip(invitations_responses, messages):
            mess_data = mess.json()
            if mess_data["items"][0]["author"]["participant_type"] == "employer":
                del invitations_responses[invitations_responses.index(response)]
                del messages[messages.index(mess)]
                continue
            response["message"] = mess_data["items"][0]["text"]
        return [
            self._serialize_data_response_to_vacancy(response)
            for response in invitations_responses
        ]

    async def get_user_rules(self) -> dict:
        rules = {
            "rule_1": "Длина отклика не более 800 символов. Допускается отклонение +- 20 символов"
        }
        return rules

    async def data_collect_for_llm(
        self,
        user_id: int,
        vacancy_id: str,
        resume_id: str,
    ) -> GenerateResponseData:
        vacancy_data = await self.get_vacancy_data(vacancy_id)
        tasks = [
            self.get_employer_data(vacancy_data.employer_id),
            self.get_resume_data(resume_id),
            self.get_user_rules(),
            self.get_good_responses(),
        ]
        result = await asyncio.gather(*tasks)
        return GenerateResponseData(
            user_id=user_id,
            vacancy=vacancy_data,
            employer=result[0],
            resume=result[1],
            user_rules=result[2],
            good_responses=result[3],
        )

    async def send_response_to_vacancy(self, response: ResponseToVacancyEntity) -> bool:
        return await self.hh_client.apply_to_vacancy(
            resume_id=response.resume_id,
            vacancy_id=response.vacancy_id,
            message=response.message,
        )
