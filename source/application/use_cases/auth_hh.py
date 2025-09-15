from typing import Mapping, Any

from source.application.services.hh_service import IHHService, AuthTokens
from source.application.services.state_manager import IStateManager, URL



class OAuthHHUseCase:

    def __init__(self, hh_service: IHHService, state_manager: IStateManager):
        self.hh_service = hh_service
        self.state_manager = state_manager

    async def __call__(self, code: str, state: str, request: Mapping[str, Any]) -> tuple[URL, AuthTokens]:
        tokens = await self.hh_service.auth(code)
        payload = await self.hh_service.get_me()
        redirect_url = await self.state_manager.state_convert(state, payload.model_dump(), request)
        return redirect_url, tokens
