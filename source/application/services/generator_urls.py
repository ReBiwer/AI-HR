from abc import ABC, abstractmethod


class IGeneratorRedirectURL[ReqType](ABC):

    @abstractmethod
    async def telegram_url(self, state: str) -> str:
        """URL ссылка для редиректа в телеграмм"""
        ...

    @abstractmethod
    def backend_url(self, request: ReqType, state: str) -> str:
        """URL ссылка для редиректа на ручку бекенда"""
        ...
