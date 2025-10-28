import re
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from aiogram.fsm.context import FSMContext

from source.domain.entities.user import UserEntity
from source.presentation.bot.storage_keys import StorageKeys


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки авторизации пользователя в HH.ru.

    Пропускает команды /start и /help без проверки.
    Для остальных команд проверяет наличие валидных токенов.
    """

    # Команды, которые не требуют авторизации
    PUBLIC_COMMANDS = {"/start", "/help"}
    PRIVATE_PATTERN = {
        re.compile(
            r"(?:https?://)?(?:[\w-]+\.)*hh\.ru/vacancy/(?P<vacancy_id>\d+)(?:[/?#][^\s.,!?)]*)?"
        )
    }

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any],
    ) -> Any:
        """
        Обработчик middleware.

        Args:
            handler: Следующий обработчик в цепочке
            message: Сообщение от Telegram
            data: Данные контекста

        Returns:
            Результат выполнения handler или None, если авторизация не пройдена
        """

        # Проверяем текст сообщение на приватность
        check_match_to_patterns = any(
            bool(pattern.fullmatch(message.text)) for pattern in self.PRIVATE_PATTERN
        )
        if (
            any(message.text.startswith(cmd) for cmd in self.PUBLIC_COMMANDS)
            and not check_match_to_patterns
        ):
            return await handler(message, data)

        # Получаем FSM context
        state: FSMContext = data.get("state")
        data_state = await state.get_data()
        if StorageKeys.USER_INFO in data_state and data_state[StorageKeys.USER_INFO]:
            data[StorageKeys.USER_INFO] = UserEntity.model_validate_json(
                data_state[StorageKeys.USER_INFO]
            )
            return await handler(message, data)

        await message.answer(
            "Необходимо авторизоваться.\n" "Используйте команду /start для начала."
        )
        return None
