from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from dishka import FromDishka

from source.presentation.bot.storage_keys import StorageKeys
from source.presentation.bot.utils.token_manager import TokenManager
from source.application.services.hh_service import IHHService

router = Router()


@router.message(Command("profile"))
async def show_profile(
    message: Message,
    state: FSMContext,
    hh_service: FromDishka[IHHService],
):
    """
    Показывает профиль пользователя HH.ru.

    Демонстрирует:
    - Получение токена из storage
    - Использование токена для API запроса
    - Обработку ошибок авторизации
    """
    token_manager = TokenManager(state)

    # Получаем токен
    access_token = await token_manager.get_access_token()

    if not access_token:
        await message.answer(
            "⚠️ Токен авторизации не найден или истек.\n"
            "Пожалуйста, авторизуйтесь заново: /start"
        )
        return

    # Используем токен для запроса к API
    # (предполагается, что в hh_service есть метод для получения профиля)
    try:
        # Здесь должен быть реальный запрос к HH API
        # Например: user_data = await hh_service.get_user_me(access_token)

        # Получаем сохраненную информацию
        user_info = await token_manager.get_user_info()

        # Проверяем, не истекает ли скоро токен
        needs_refresh = await token_manager.needs_refresh()
        token_status = "⚠️ Скоро истечет" if needs_refresh else "✅ Активен"

        await message.answer(
            f"👤 <b>Ваш профиль HH.ru</b>\n\n"
            f"ID: {user_info.hh_id}\n"
            f"Имя: {user_info.name}\n"
            f"Отчество: {user_info.mid_name}\n\n"
            f"Статус токена: {token_status}"
        )

    except Exception as e:
        await message.answer(
            f"⚠️ Ошибка при получении профиля: {str(e)}\n"
            "Попробуйте авторизоваться заново: /start"
        )
        # При ошибке авторизации можно очистить токены
        await token_manager.clear_tokens()


@router.message(Command("logout"))
async def logout(message: Message, state: FSMContext):
    """
    Выход из аккаунта (очистка информации о пользователе их FSMContext).
    """
    await state.set_data({StorageKeys.USER_INFO: None})

    await message.answer(
        "👋 Вы успешно вышли из аккаунта.\n\n" "Для повторной работы используйте /start"
    )
