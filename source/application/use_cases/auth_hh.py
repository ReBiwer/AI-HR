from typing import Mapping, Any

from source.application.repositories.user import IUserRepository
from source.application.services.hh_service import IHHService, AuthTokens
from source.application.services.state_manager import IStateManager, URL
from source.domain.entities.user import UserEntity


class OAuthHHUseCase:
    def __init__(
        self,
        hh_service: IHHService,
        state_manager: IStateManager,
        repository: IUserRepository[UserEntity],
    ):
        self.hh_service = hh_service
        self.state_manager = state_manager
        self.user_repo = repository

    async def __call__(
        self, code: str, state: str, request: Mapping[str, Any], subject
    ) -> tuple[URL, AuthTokens]:
        tokens = await self.hh_service.auth(code)
        user = await self.hh_service.get_me(subject)
        payload = await self.user_repo.create(user)
        converted_payload = f"id={payload.id}, name={payload.name}"
        redirect_url = await self.state_manager.state_convert(
            state, converted_payload, request
        )
        return redirect_url, tokens
