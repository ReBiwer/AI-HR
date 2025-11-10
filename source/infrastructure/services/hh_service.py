import asyncio
import httpx
from typing import Optional, Dict, Any

from httpx import Response
from hh_api.auth import TokenPair
from hh_api.exceptions import HHAPIError, HHAuthError, HHNetworkError
from hh_api.client import HHClient, TokenManager, Subject

from source.application.services.ai_service import GenerateResponseData
from source.domain.entities.employer import EmployerEntity
from source.domain.entities.user import UserEntity
from source.domain.entities.vacancy import VacancyEntity
from source.application.services.hh_service import IHHService, AuthTokens
from source.domain.entities.response import ResponseToVacancyEntity
from source.domain.entities.resume import ResumeEntity


class CustomHHClient(HHClient):
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

    @staticmethod
    def _check_status_code_response(response: Response) -> None:
        """Проверяет наличие ошибок в запросе"""
        # авторизационные ошибки пробрасываем как HHAuthError
        if response.status_code in (401, 403):
            # У многих интеграций это значит «нужно переавторизовать пользователя».
            raise HHAuthError(response.status_code, response.text)

        if response.status_code >= 400:
            raise HHAPIError(response.status_code, response.text)

        response.raise_for_status()

    async def authorization(self, tokens: TokenPair) -> dict[str, Any]:
        url_user = f"{self.base_url}/me"
        url_resumes = f"{self.base_url}/resumes/mine"
        last_exc: Optional[Exception] = None
        req_headers = {
            "Authorization": f"Bearer {tokens.access_token}",
            "User-Agent": self.user_agent,
        }
        for attempt in range(1, self.retries + 1):
            try:
                # Получаем информацию о пользователе
                resp_user = await self._client.request(
                    "GET",
                    url_user,
                    headers=req_headers,
                )
                self._check_status_code_response(resp_user)
                user_data = resp_user.json()

                # Получаем список резюме пользователя
                resp_resumes_user = await self._client.request(
                    "GET",
                    url_resumes,
                    headers=req_headers,
                )
                self._check_status_code_response(resp_resumes_user)
                # Запрашиваем детальную информацию по каждому резюме
                resumes_data: list[Response] = await asyncio.gather(
                    *[
                        self._client.request(
                            "GET",
                            f"{self.base_url}/resumes/{data["id"]}",
                            headers=req_headers,
                        )
                        for data in resp_resumes_user.json()["items"]
                    ]
                )
                for response in resumes_data:
                    self._check_status_code_response(response)
                # Добавляем информацию о резюме к общей инфе о пользователе
                user_data["resumes_data"] = [resume.json() for resume in resumes_data]
                return user_data

            except httpx.RequestError as e:
                last_exc = e
                if attempt < self.retries:
                    await asyncio.sleep(self.backoff_base * (2 ** (attempt - 1)))
                    continue
                raise HHNetworkError(str(e)) from e

            except HHAPIError as e:
                last_exc = e
                # 5xx — можно попробовать повторить
                if 500 <= getattr(e, "status_code", 0) < 600 and attempt < self.retries:
                    await asyncio.sleep(self.backoff_base * (2 ** (attempt - 1)))
                    continue
                raise

        assert last_exc is not None
        raise last_exc

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


class CustomTokenManager(TokenManager):
    async def exchange_auth_code(self, code: str) -> TokenPair:
        data = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": self.config.redirect_uri,
        }
        headers = {"User-Agent": self.user_agent}
        resp = await self._post_with_retry(
            self.config.token_url, data=data, headers=headers
        )
        payload = resp.json()
        tokens = self._tokenpair_from_payload(payload)
        return tokens

    async def save_tokens(self, subject: Subject, tokens: TokenPair) -> None:
        await self.store.set_tokens(subject, tokens)


class HHService(IHHService):
    def __init__(self, token_manager: CustomTokenManager):
        self._hh_tm = token_manager
        self.hh_client = CustomHHClient(self._hh_tm)

    def get_auth_url(self, state: str):
        return self._hh_tm.authorization_url(state)

    async def aclose_hh_client(self):
        await self.hh_client.aclose()

    async def auth(self, code: str) -> tuple[UserEntity, AuthTokens]:
        tokens = await self._hh_tm.exchange_auth_code(code)
        resp = await self.hh_client.authorization(tokens)
        auth_user = self._serialize_data_user(resp)
        await self._hh_tm.save_tokens(auth_user.hh_id, tokens)
        return auth_user, AuthTokens(
            access_token=tokens.access_token, refresh_token=tokens.refresh_token
        )

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

    async def get_vacancies(
        self, subject: Optional[Subject], **filter_query
    ) -> list[VacancyEntity]:
        vacancies = await self.hh_client.get_vacancies(subject, **filter_query)
        result = await asyncio.gather(
            *[
                self.get_vacancy_data(subject, vacancy["id"])
                for vacancy in vacancies["items"]
            ]
        )
        return result

    async def get_vacancy_data(
        self, subject: Optional[Subject], vacancy_id: str
    ) -> VacancyEntity:
        data = await self.hh_client.get_vacancy(vacancy_id, subject=subject)
        return self._serialize_data_vacancy(data)

    async def get_employer_data(
        self, subject: Optional[Subject], employer_id: str
    ) -> EmployerEntity:
        data = await self.hh_client.get_employer(employer_id, subject=subject)
        return self._serialize_data_employer(data)

    async def get_resume_data(
        self, subject: Optional[Subject], resume_id: str
    ) -> ResumeEntity:
        data = await self.hh_client.get_resume(resume_id, subject=subject)
        return self._serialize_data_resume(data)

    async def get_user_rules(self) -> dict:
        rules = {
            "rule_1": "Длина отклика не более 800 символов. Допускается отклонение +- 20 символов"
        }
        return rules

    async def data_collect_for_llm(
        self,
        subject: Optional[Subject],
        user_id: int,
        vacancy_id: str,
        resume_id: str,
    ) -> GenerateResponseData:
        vacancy_data = await self.get_vacancy_data(subject, vacancy_id)
        tasks = [
            self.get_employer_data(subject, vacancy_data.employer_id),
            self.get_resume_data(subject, resume_id),
            self.get_user_rules(),
        ]
        result = await asyncio.gather(*tasks)
        return GenerateResponseData(
            user_id=user_id,
            vacancy=vacancy_data,
            employer=result[0],
            resume=result[1],
            user_rules=result[2],
        )

    async def send_response_to_vacancy(self, response: ResponseToVacancyEntity) -> bool:
        return await self.hh_client.apply_to_vacancy(
            resume_id=response.resume_hh_id,
            vacancy_id=response.vacancy_hh_id,
            message=response.message,
        )
