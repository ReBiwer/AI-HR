from source.application.services.hh_service import IHHService, AuthTokens


class OAuthHHUseCase:

    def __init__(self, hh_service: IHHService):
        self.hh_service = hh_service

    async def __call__(self, code: str) -> AuthTokens:
        tokens = await self.hh_service.auth(code)
        return tokens
