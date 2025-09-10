from dishka import Provider, Scope, provide

from source.infrastructure.services.hh_service import HHService
from source.infrastructure.services.ai_service import AIService
from source.application.services.hh_service import IHHService
from source.application.services.ai_service import IAIService


class ServicesProviders(Provider):
    @provide
    def get_hh_service(self) -> IHHService:
        return HHService()

    @provide
    def get_ai_service(self) -> IAIService:
        return AIService()
