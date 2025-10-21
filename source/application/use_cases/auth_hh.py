from typing import Mapping, Any

from source.application.repositories.user import IUserRepository
from source.application.repositories.base import IUnitOfWork
from source.application.services.hh_service import IHHService, AuthTokens
from source.application.services.state_manager import IStateManager, URL
from source.domain.entities.user import UserEntity


class OAuthHHUseCase:
    def __init__(
        self,
        hh_service: IHHService,
        state_manager: IStateManager,
        class_repo: type[IUserRepository[UserEntity]],
        uow: IUnitOfWork,
    ):
        self.hh_service = hh_service
        self.state_manager = state_manager
        self.uow = uow
        self.class_repo = class_repo

    async def __call__(
        self, code: str, state: str, request: Mapping[str, Any], subject
    ) -> tuple[URL, AuthTokens]:
        user, tokens = await self.hh_service.auth(code)

        async with self.uow as session:
            repo = self.class_repo(session)
            payload = await repo.create(user)

        converted_payload = payload.model_dump_json(include={"id", "name"})
        redirect_url = await self.state_manager.state_convert(
            state, converted_payload, request
        )
        return redirect_url, tokens
