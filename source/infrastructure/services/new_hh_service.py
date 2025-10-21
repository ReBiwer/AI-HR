import datetime
import json
from urllib import parse
from typing import Any, Union
from dataclasses import dataclass
from redis.asyncio.client import Redis
from httpx import AsyncClient, Client, Response

from source.application.services.ai_service import GenerateResponseData
from source.application.services.hh_service import AuthTokens, IHHService
from source.domain.entities.employer import EmployerEntity
from source.domain.entities.response import ResponseToVacancyEntity
from source.domain.entities.resume import ResumeEntity
from source.domain.entities.user import UserEntity
from source.domain.entities.vacancy import VacancyEntity


@dataclass(frozen=True)
class AuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    user_agent: str
    authorize_url: str = "https://hh.ru/oauth/authorize"
    token_url: str = "https://api.hh.ru/token"
    base_url: str = "https://api.hh.ru"

    def get_full_url(self, path: str, **params) -> str:
        url_pars = parse.urlparse(self.base_url)
        if params:
            str_params = "&".join([f"{k}={v}" for k, v in params.items()])
            return parse.urlunparse(
                (
                    url_pars.scheme,
                    url_pars.netloc,
                    path,
                    "",
                    str_params,
                    url_pars.fragment,
                )
            )
        return parse.urlunparse(
            (
                url_pars.scheme,
                url_pars.netloc,
                path,
                "",
                url_pars.params,
                url_pars.fragment,
            )
        )

    def get_auth_url(self, state: str, redirect_uri: str | None = None) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "state": state,
        }
        return f"{self.authorize_url}?{parse.urlencode(params)}"


class TokenManager:
    def __init__(
        self, config: AuthConfig, redis_client: Redis, http_client: Client = None
    ):
        self.conf = config
        self.redis = redis_client
        self.client = http_client if http_client else AsyncClient(timeout=20.0)

    async def _post_with_retry(
        self, url: str, data: dict[str, Any], headers: dict[str, str]
    ) -> Response:
        resp = await self.client.post(url, data=data, headers=headers)
        resp.raise_for_status()
        return resp

    @staticmethod
    def _auth_tokens_from_payload(payload: dict[str, Any]) -> AuthTokens:
        access = payload.get("access_token")
        if not access:
            raise RuntimeError("В ответе нет access_token")
        expires_in = int(payload.get("expires_in")) or 0
        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            seconds=expires_in
        )
        return AuthTokens(
            access_token=access,
            refresh_token=payload.get("refresh_token") or None,
            expires_in=expires_in,
            expire_at=expires_at,
        )

    async def exchange_code(self, code: str) -> AuthTokens:
        data = {
            "grant_type": "authorization_code",
            "client_id": self.conf.client_id,
            "client_secret": self.conf.client_secret,
            "code": code,
            "redirect_uri": self.conf.redirect_uri,
        }
        headers = {"User-Agent": self.conf.user_agent}
        resp = await self.client.post(self.conf.token_url, data=data, headers=headers)
        payload = resp.json()
        tokens = self._auth_tokens_from_payload(payload)
        return tokens

    async def save_tokens(self, subject: str, tokens: AuthTokens) -> None:
        data = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
            "expires_at": tokens["expire_at"].isoformat(),
        }
        await self.redis.set(subject, json.dumps(data, ensure_ascii=False))

    async def get_tokens(self, subject: str) -> AuthTokens:
        raw = await self.redis.get(subject)
        data = json.loads(raw)
        return AuthTokens(
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in"),
            expire_at=datetime.datetime.fromisoformat(data.get("expires_at")),
        )


class NewHHService(IHHService):
    def __init__(
        self,
        config: AuthConfig,
        token_manager: TokenManager,
        http_client: AsyncClient | None = None,
    ):
        self._conf = config
        self._token_manager = token_manager
        self._http_client = http_client if http_client else AsyncClient(timeout=20.0)

    def get_auth_url(self, state: str) -> str: ...

    async def get_me(self, subject: Union[int, str]) -> UserEntity: ...

    async def auth(self, subject: Union[int, str], code: str) -> AuthTokens: ...

    async def get_vacancy_data(
        self, subject: Union[int, str], vacancy_id: str
    ) -> VacancyEntity: ...

    async def get_employer_data(
        self, subject: Union[int, str], employer_id: str
    ) -> EmployerEntity: ...

    async def get_resume_data(
        self, subject: Union[int, str], resume_id: str
    ) -> ResumeEntity: ...

    async def get_good_responses(
        self, subject: Union[int, str], quantity_responses: int = 10
    ) -> list[ResponseToVacancyEntity]: ...

    async def get_user_rules(self) -> dict: ...

    async def data_collect_for_llm(
        self,
        subject: Union[int, str],
        user_id: int,
        vacancy_id: str,
        resume_id: str,
    ) -> GenerateResponseData: ...

    async def send_response_to_vacancy(
        self, response: ResponseToVacancyEntity
    ) -> bool: ...
