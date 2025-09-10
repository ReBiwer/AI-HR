from dishka import Provider, Scope, provide

from source.infrastructure.services.hh_service import HHService
from source.infrastructure.services.ai_service import AIService
from source.application.services.hh_service import IHHService
from source.application.services.ai_service import IAIService
from source.application.use_cases.generate_response import GenerateResponseUseCase
from source.application.use_cases.auth_hh import OAuthHHUseCase


class ServicesProviders(Provider):
    @provide
    def get_hh_service(self) -> IHHService:
        return HHService()

    @provide
    def get_ai_service(self) -> IAIService:
        return AIService()


class UseCasesProviders(Provider):
    @provide
    def get_generate_response_use_case(
        self,
        hh_service: IHHService,
        ai_service: IAIService,
        ) -> GenerateResponseUseCase:
        return GenerateResponseUseCase(hh_service, ai_service)

    @provide
    def get_oauth_hh_use_case(self, hh_service: IHHService) -> OAuthHHUseCase:
        return OAuthHHUseCase(hh_service)