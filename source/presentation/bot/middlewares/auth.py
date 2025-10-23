"""
Middleware для проверки авторизации пользователя.

Этот middleware проверяет наличие токенов авторизации HH.ru
и их валидность перед обработкой команд, требующих авторизации.

Почему middleware:
- Централизованная логика проверки авторизации
- Не нужно дублировать проверки в каждом обработчике
- Автоматическая обработка истекших токенов
- Чистый код в handlers
"""

from typing import Any, Awaitable, Callable, Dict
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from aiogram.fsm.context import FSMContext

from source.presentation.bot.storage_keys import StorageKeys


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки авторизации пользователя в HH.ru.

    Пропускает команды /start и /help без проверки.
    Для остальных команд проверяет наличие валидных токенов.
    """

    # Команды, которые не требуют авторизации
    PUBLIC_COMMANDS = {"/start", "/help"}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Обработчик middleware.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие от Telegram
            data: Данные контекста

        Returns:
            Результат выполнения handler или None, если авторизация не пройдена
        """
        # Если это не сообщение, пропускаем проверку
        if not isinstance(event, Message):
            return await handler(event, data)

        message: Message = event

        # Проверяем, является ли команда публичной
        if message.text and any(
            message.text.startswith(cmd) for cmd in self.PUBLIC_COMMANDS
        ):
            return await handler(event, data)

        # Получаем FSM context
        state: FSMContext = data.get("state")
        if not state:
            # Если нет state context, пропускаем (не должно происходить)
            return await handler(event, data)

        # Проверяем наличие токена
        user_data = await state.get_data()
        access_token = user_data.get(StorageKeys.HH_ACCESS_TOKEN)

        if not access_token:
            await message.answer(
                "⚠️ Для использования этой команды необходимо авторизоваться.\n"
                "Используйте команду /start для начала."
            )
            return None

        # Проверяем срок действия токена
        expires_at = user_data.get(StorageKeys.HH_TOKEN_EXPIRES_AT)
        if expires_at and datetime.now().timestamp() > expires_at:
            await message.answer(
                "⚠️ Ваш токен авторизации истек.\n"
                "Пожалуйста, авторизуйтесь заново с помощью команды /start"
            )
            # Очищаем устаревшие данные
            await state.update_data(
                {
                    StorageKeys.HH_ACCESS_TOKEN: None,
                    StorageKeys.HH_REFRESH_TOKEN: None,
                    StorageKeys.HH_TOKEN_EXPIRES_AT: None,
                }
            )
            return None

        # Добавляем токен в data для удобного доступа в handlers
        data["hh_access_token"] = access_token
        data["hh_user_data"] = user_data

        return await handler(event, data)
