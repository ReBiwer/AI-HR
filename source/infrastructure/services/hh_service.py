import re
import asyncio
from fake_useragent import UserAgent
from hh_api.auth.keyed_stores import InMemoryKeyedTokenStore
from hh_api.auth.token_manager import OAuthConfig
from hh_api.client import HHClient, TokenManager

from source.domain.entities.employer import EmployerEntity
from source.domain.entities.vacancy import Experience, VacancyEntity
from source.infrastructure.settings.app import app_settings
from source.application.services.hh_service import IHHService, AuthTokens
from source.domain.entities.response import ResponseToVacancyEntity
from source.domain.entities.resume import ResumeEntity, ContactEntity, ExperienceEntity


class HHService(IHHService):

    def __init__(self):
        self._oath_config = OAuthConfig(
            client_id=app_settings.HH_CLIENT_ID,
            client_secret=app_settings.HH_CLIENT_SECRET,
            redirect_uri=app_settings.HH_REDIRECT_URI
        )
        self._user_agent = UserAgent().chrome
        self._keyed_store = InMemoryKeyedTokenStore()
        self._hh_tm = TokenManager(
            config= self._oath_config,
            store=self._keyed_store,
            user_agent=self._user_agent
        )
        self.hh_client = HHClient(self._hh_tm, subject=app_settings.HH_FAKE_SUBJECT)

    @staticmethod
    def _serialize_data_vacancy(data: dict) -> VacancyEntity:
        vacancy_data = {
            "name": data["name"],
            "experience": {
                Experience(id=exp['id'], name=exp['name'])
                for exp in data["experience"]
            },
            "description": data["description"],
            "key_skills": data["key_skills"]
        }
        return VacancyEntity.model_validate(vacancy_data)

    @staticmethod
    def _serialize_data_employer(data: dict) -> EmployerEntity:
        employer_data = {}
        return EmployerEntity.model_validate(employer_data)

    @staticmethod
    def _serialize_data_resume(data: dict) -> ResumeEntity:
        contact_data = {
            f"{contact['kind']}": contact['contact_value']
            for contact in data["contact"]
        }
        resume_data = {
            "name": data["first_name"],
            "surname": data["last_name"],
            "job_description": [
                ExperienceEntity.model_validate(experience)
                for experience in data["experience"]
            ],
            "skills": data["skill_set"],
            "contacts": ContactEntity.model_validate(contact_data)
        }
        return ResumeEntity.model_validate(resume_data)

    @staticmethod
    def _serialize_data_response_to_vacancy(data: dict) -> ResponseToVacancyEntity:
        response_data = {
            "url_vacancy": data["url"],
            "vacancy_id": data["id"],
            "resume_id": data["resume"]["id"],
            "message": data["message"]
        }
        return ResponseToVacancyEntity.model_validate(response_data)

    @staticmethod
    def extract_vacancy_id_from_url(url: str) -> str:
        pattern = r"/https?:\/\/[^\/]+\.hh\.ru\/vacancy\/(\d+)/gm"
        match = re.search(pattern, url)
        return match.group(1)

    def get_auth_url(self):
        return self._hh_tm.authorization_url()

    async def auth(self, code: str) -> AuthTokens:
        tokens = await self._hh_tm.exchange_code(app_settings.HH_FAKE_SUBJECT, code=code)
        return AuthTokens(access_token=tokens.access_token, refresh_token=tokens.refresh_token)

    async def get_vacancy_data(self, vacancy_id: str) -> VacancyEntity:
        data = await self.hh_client.get_vacancy(vacancy_id)
        return self._serialize_data_vacancy(data)

    async def get_employer_data(self, employer_id: str) -> EmployerEntity:
        data = (await self.hh_client._request("GET", f"/employers/{employer_id}")).json()
        return self._serialize_data_employer(data)

    async def get_resume_data(self, resume_id: str) -> ResumeEntity:
        data = await self.hh_client.get_resume(resume_id)
        return self._serialize_data_resume(data)

    async def get_good_responses(self, quantity_responses: int = 10) -> list[ResponseToVacancyEntity]:
        data = (await self.hh_client._request(
            "GET",
            "/negotiations",
            params={"status": "invitations"}
        )).json()

        # создаем корутины для подгрузки сообщений откликов
        load_messages = [
            self.hh_client._request("GET", f"/negotiations/{response['id']}/messages")
            for response in data["items"]
        ]
        # конкурентно выполняем каждый запрос на подгрузку сообщений
        messages = await asyncio.gather(*load_messages)
        # добавляем отклик (первое сообщение в переписке) в список
        for response, mess in zip(data["items"], messages):
            response["message"] = mess["items"][-1]["text"]
        return [
            self._serialize_data_response_to_vacancy(response)
            for response in data["items"]
        ]

    async def get_user_rules(self) -> dict:
        rules = {
            "rule_1": "Длина отклика не более 800 символов. Допускается отклонение +- 20 символов"
        }
        return rules

    async def send_response_to_vacancy(self, response: ResponseToVacancyEntity) -> bool:
        return await self.hh_client.apply_to_vacancy(
            resume_id=response.resume_id,
            vacancy_id=response.vacancy_id,
            message=response.message
        )
