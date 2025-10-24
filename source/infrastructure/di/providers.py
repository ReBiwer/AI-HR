from typing import AsyncGenerator

from aiogram.fsm.context import FSMContext
from dishka import Provider, Scope, provide
from dishka.integrations.aiogram import AiogramMiddlewareData
from redis.asyncio.client import Redis
from hh_api.auth import OAuthConfig, RedisKeyedTokenStore, KeyedTokenStore
from langgraph.checkpoint.memory import BaseCheckpointSaver
from langgraph.checkpoint.redis import AsyncRedisSaver

from source.presentation.bot.storage_keys import StorageKeys
from source.infrastructure.db.engine import async_session_maker
from source.infrastructure.settings.app import app_settings
from source.infrastructure.db.repositories.user import UserRepository
from source.infrastructure.db.repositories.resume import (
    ResumeRepository,
    JobExperienceRepository,
)
from source.infrastructure.db.uow import UnitOfWork
from source.infrastructure.services.hh_service import HHService, CustomTokenManager
from source.infrastructure.services.ai_service import AIService
from source.infrastructure.services.state_manager import StateManager
from source.application.repositories.user import IUserRepository
from source.application.repositories.resume import (
    IResumeRepository,
    IJobExperienceRepository,
)
from source.application.repositories.base import IUnitOfWork
from source.application.services.hh_service import IHHService
from source.application.services.ai_service import IAIService
from source.application.services.state_manager import IStateManager
from source.application.use_cases.generate_response import GenerateResponseUseCase
from source.application.use_cases.regenerate_response import RegenerateResponseUseCase
from source.application.use_cases.auth_hh import OAuthHHUseCase
from source.domain.entities.user import UserEntity


class ServicesProviders(Provider):
    scope = Scope.APP

    @provide
    def oauth_config(self) -> OAuthConfig:
        return OAuthConfig(
            client_id=app_settings.HH_CLIENT_ID,
            client_secret=app_settings.HH_CLIENT_SECRET,
            redirect_uri=app_settings.HH_REDIRECT_URI,
            token_url="https://api.hh.ru/token",
        )

    @provide
    def keyed_store(self) -> KeyedTokenStore:
        redis_client = Redis()
        return RedisKeyedTokenStore(redis_client)

    @provide
    def custom_token_manager(
        self, config: OAuthConfig, keyed_store: KeyedTokenStore
    ) -> CustomTokenManager:
        return CustomTokenManager(
            config=config,
            store=keyed_store,
            user_agent="AI HR/1.0 (bykov100898@yandex.ru)",
        )

    @provide
    def get_hh_service(self, token_manager: CustomTokenManager) -> IHHService:
        return HHService(token_manager)

    @provide
    async def get_checkpointer(self) -> AsyncGenerator[BaseCheckpointSaver, None]:
        async with AsyncRedisSaver.from_conn_string(
            app_settings.redis_url,
            ttl={"default_ttl": app_settings.REDIS_CHECKPOINT_TTL},
        ) as checkpointer:
            await checkpointer.asetup()
            yield checkpointer

    @provide
    def get_ai_service(self, checkpointer: BaseCheckpointSaver) -> IAIService:
        return AIService(checkpointer)

    @provide
    def get_generate_urls_service(self) -> IStateManager:
        return StateManager()


class UseCasesProviders(Provider):
    scope = Scope.REQUEST

    @provide
    def get_generate_response_use_case(
        self,
        hh_service: IHHService,
        ai_service: IAIService,
    ) -> GenerateResponseUseCase:
        return GenerateResponseUseCase(hh_service, ai_service)

    @provide
    def get_regenerate_response_use_case(
        self,
        hh_service: IHHService,
        ai_service: IAIService,
    ) -> RegenerateResponseUseCase:
        return RegenerateResponseUseCase(hh_service, ai_service)

    @provide
    def get_oauth_hh_use_case(
        self,
        hh_service: IHHService,
        state_manager: IStateManager,
        repository: type[IUserRepository],
        uow: IUnitOfWork,
    ) -> OAuthHHUseCase:
        return OAuthHHUseCase(hh_service, state_manager, repository, uow)


class RepositoriesProviders(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_async_session(self) -> IUnitOfWork:
        async with async_session_maker() as session:
            return UnitOfWork(session)

    @provide
    def get_user_repository(self) -> type[IUserRepository]:
        return UserRepository

    @provide
    def get_resume_repository(self) -> type[IResumeRepository]:
        return ResumeRepository

    @provide
    def get_job_experience_repository(self) -> type[IJobExperienceRepository]:
        return JobExperienceRepository


class BotProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_user_bot(
        self, middleware_data: AiogramMiddlewareData
    ) -> UserEntity | None:
        state: FSMContext = middleware_data.get("state")
        data_state = await state.get_data()
        if StorageKeys.USER_INFO in data_state and data_state[StorageKeys.USER_INFO]:
            return UserEntity.model_validate_json(data_state[StorageKeys.USER_INFO])
        return None
