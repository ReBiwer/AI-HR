from typing import Mapping, Any
from abc import ABC, abstractmethod

type URL = str


class IStateManager(ABC):

    @abstractmethod
    async def state_convert(self, state: str, payload: str, request: Mapping[str, Any]) -> URL:
        """Метод для конвертации состояния"""
        ...
