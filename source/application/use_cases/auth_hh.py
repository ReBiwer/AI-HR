from source.application.services.hh_service import IHHService, AuthTokens


class AuthHHUseCase:

    def __init__(self, hh_service: IHHService):
        self.hh_service = hh_service

    async def __call__(self) -> AuthTokens:
        tokens = await self.hh_service.auth()
        return tokens
