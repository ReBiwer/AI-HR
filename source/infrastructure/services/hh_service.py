from fake_useragent import UserAgent
from hh_api.auth.keyed_stores import InMemoryKeyedTokenStore
from hh_api.auth.token_manager import OAuthConfig
from hh_api.client import HHClient, TokenManager

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
    def _extract_data_resume(data: dict) -> ResumeEntity:
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

    def get_auth_url(self):
        return self._hh_tm.authorization_url()

    async def auth(self, code: str) -> AuthTokens:
        tokens = await self._hh_tm.exchange_code(app_settings.HH_FAKE_SUBJECT, code=code)
        return AuthTokens(access_token=tokens.access_token, refresh_token=tokens.refresh_token)

    async def get_resume(self, resume_id: str) -> ResumeEntity:
        result = await self.hh_client.get_resume(resume_id)
        return self._extract_data_resume(result)

    async def get_resumes(self) -> list[ResumeEntity]:
        results: dict = (await self.hh_client._request("GET", "/resumes/mine")).json()
        return [ResumeEntity.model_validate(resume) for resume in results["items"]]

    async def send_response_to_vacancy(self, response: ResponseToVacancyEntity) -> bool:
        return await self.hh_client.apply_to_vacancy(
            resume_id=response.resume_id,
            vacancy_id=response.vacancy_id,
            message=response.message
        )
