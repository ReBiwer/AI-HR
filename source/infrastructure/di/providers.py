from typing import AsyncGenerator
from dishka import Provider, Scope, provide
from langgraph.checkpoint.memory import BaseCheckpointSaver
from langgraph.checkpoint.redis import AsyncRedisSaver

from source.infrastructure.db.engine import async_session_maker
from source.infrastructure.settings.app import app_settings
from source.infrastructure.db.repositories.user import UserRepository
from source.infrastructure.db.repositories.resume import (
    ResumeRepository,
    JobExperienceRepository,
)
from source.infrastructure.db.uow import UnitOfWork
from source.infrastructure.services.hh_service import HHService
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


class ServicesProviders(Provider):
    scope = Scope.APP

    @provide
    def get_hh_service(self) -> IHHService:
        return HHService()

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
