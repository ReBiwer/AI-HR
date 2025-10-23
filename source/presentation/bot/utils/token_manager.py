"""
Менеджер для работы с токенами авторизации в FSM storage.

Этот модуль предоставляет удобный интерфейс для сохранения, получения
и валидации токенов авторизации HH.ru.

Почему отдельный класс:
- Инкапсуляция логики работы с токенами
- Единая точка доступа к токенам
- Легко тестировать
- Легко добавлять новую функциональность (например, автообновление токенов)
- Соблюдение принципа Single Responsibility
"""

from typing import Optional
from datetime import datetime

from aiogram.fsm.context import FSMContext

from source.presentation.bot.schemas import TGUser
from source.presentation.bot.storage_keys import StorageKeys


class TokenManager:
    """
    Менеджер для работы с токенами авторизации HH.ru.

    Предоставляет методы для сохранения, получения и валидации токенов.
    """

    def __init__(self, state: FSMContext):
        """
        Инициализация менеджера токенов.

        Args:
            state: FSM context для работы с хранилищем
        """
        self._state = state

    async def save_tokens(
        self,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        token_type: str = "Bearer",
        user_info: Optional[TGUser] = None,
    ) -> None:
        """
        Сохранить токены авторизации в storage.

        Args:
            access_token: Access токен от HH.ru
            refresh_token: Refresh токен для обновления access токена
            expires_in: Время жизни токена в секундах
            token_type: Тип токена (обычно "Bearer")
            user_info: Дополнительная информация о пользователе (опционально)

        Почему expires_at вычисляется здесь:
        - expires_in - это относительное время от момента получения токена
        - Сохраняем абсолютное время (timestamp), чтобы легко проверять валидность
        - Не зависит от часовых поясов (используем timestamp)
        """
        expires_at = datetime.now().timestamp() + expires_in

        # Подготавливаем данные для сохранения
        token_data = {
            StorageKeys.HH_ACCESS_TOKEN: access_token,
            StorageKeys.HH_REFRESH_TOKEN: refresh_token,
            StorageKeys.HH_TOKEN_EXPIRES_AT: expires_at,
            StorageKeys.HH_TOKEN_TYPE: token_type,
        }

        # Добавляем информацию о пользователе, если она есть
        if user_info:
            token_data[StorageKeys.HH_USER_ID] = user_info.hh_id
            token_data[StorageKeys.HH_USER_NAME] = user_info.name
            token_data[StorageKeys.HH_USER_MID_NAME] = user_info.mid_name

        # Сохраняем данные (update_data добавляет к существующим, не перезаписывает)
        await self._state.update_data(token_data)

    async def get_access_token(self) -> Optional[str]:
        """
        Получить access токен из storage.

        Returns:
            Access токен или None, если токен не найден или истек

        Почему проверяем валидность здесь:
        - Гарантируем, что всегда возвращаем только валидный токен
        - Избегаем использования устаревших токенов в других частях кода
        """
        if not await self.is_token_valid():
            return None

        data = await self._state.get_data()
        return data.get(StorageKeys.HH_ACCESS_TOKEN)

    async def get_refresh_token(self) -> Optional[str]:
        """
        Получить refresh токен из storage.

        Returns:
            Refresh токен или None, если не найден
        """
        data = await self._state.get_data()
        return data.get(StorageKeys.HH_REFRESH_TOKEN)

    async def is_token_valid(self) -> bool:
        """
        Проверить валидность токена.

        Returns:
            True, если токен существует и не истек, иначе False

        Почему добавляем buffer_seconds:
        - Даем небольшой запас времени (5 минут)
        - Избегаем ситуации, когда токен истекает прямо во время запроса
        - 300 секунд достаточно для выполнения большинства операций
        """
        data = await self._state.get_data()

        access_token = data.get(StorageKeys.HH_ACCESS_TOKEN)
        if not access_token:
            return False

        expires_at = data.get(StorageKeys.HH_TOKEN_EXPIRES_AT)
        if not expires_at:
            # Если нет информации о времени истечения, считаем токен невалидным
            return False

        # Добавляем небольшой буфер времени (5 минут)
        buffer_seconds = 300
        current_time = datetime.now().timestamp()

        return current_time < (expires_at - buffer_seconds)

    async def clear_tokens(self) -> None:
        """
        Очистить все токены из storage.

        Используется при выходе пользователя или при необходимости
        повторной авторизации.

        Почему обновляем через update_data, а не clear:
        - clear() удалит ВСЕ данные пользователя, включая настройки
        - update_data с None только очищает токены
        - Сохраняем другие данные пользователя (язык, настройки и т.д.)
        """
        await self._state.update_data(
            {
                StorageKeys.HH_ACCESS_TOKEN: None,
                StorageKeys.HH_REFRESH_TOKEN: None,
                StorageKeys.HH_TOKEN_EXPIRES_AT: None,
                StorageKeys.HH_TOKEN_TYPE: None,
                StorageKeys.HH_USER_ID: None,
                StorageKeys.HH_USER_MID_NAME: None,
                StorageKeys.HH_USER_NAME: None,
            }
        )

    async def get_user_info(self) -> TGUser:
        """
        Получить сохраненную информацию о пользователе HH.

        Returns:
            Словарь с информацией о пользователе
        """
        data = await self._state.get_data()

        return TGUser.model_validate(data, from_attributes=True)

    async def needs_refresh(self) -> bool:
        """
        Проверить, нужно ли обновить токен.

        Returns:
            True, если токен скоро истечет (меньше 10 минут) или уже истек

        Почему 10 минут:
        - Даем достаточно времени для обновления токена
        - Не слишком часто обновляем (экономим запросы к API)
        - Не слишком редко (избегаем истечения во время операции)
        """
        data = await self._state.get_data()

        expires_at = data.get(StorageKeys.HH_TOKEN_EXPIRES_AT)
        if not expires_at:
            return True

        # Проверяем, осталось ли меньше 10 минут
        refresh_threshold = 600  # 10 минут в секундах
        current_time = datetime.now().timestamp()

        return current_time > (expires_at - refresh_threshold)
