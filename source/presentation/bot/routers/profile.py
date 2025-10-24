from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from dishka import FromDishka

from source.presentation.bot.storage_keys import StorageKeys
from source.presentation.bot.utils.splitter import split_long_message
from source.infrastructure.services.hh_service import CustomTokenManager
from source.application.services.hh_service import IHHService
from source.domain.entities.user import UserEntity

router = Router()


@router.message(Command("profile"))
async def show_profile(
    message: Message,
    token_manager: FromDishka[CustomTokenManager],
    user: FromDishka[UserEntity | None],
    hh_service: FromDishka[IHHService],
):
    """
    Показывает информацию о пользователе
    """

    if user:
        access_token = await token_manager.ensure_access(user.hh_id)
        if not access_token:
            await message.answer(
                "⚠️ Токен авторизации не найден или истек.\n"
                "Пожалуйста, авторизуйтесь заново: /start"
            )
            return
        try:
            text_message = f"👤 <b>Ваш профиль HH.ru</b>\n\n{user}"
            chunks_message = split_long_message(text_message)
            for mess in chunks_message:
                await message.answer(mess)
        except Exception as e:
            await message.answer(
                f"⚠️ Ошибка при получении профиля: {str(e)}\n"
                "Попробуйте авторизоваться заново: /start"
            )
    else:
        await message.answer(
            "Для начала работы необходимо авторизоваться:\n"
            f"<a href='{hh_service.get_auth_url("telegram")}'>🔐 Авторизоваться в HH</a>\n\n"
        )


@router.message(Command("logout"))
async def logout(message: Message, state: FSMContext):
    """
    Выход из аккаунта (очистка информации о пользователе их FSMContext).
    """
    await state.set_data({StorageKeys.USER_INFO: None})

    await message.answer(
        "👋 Вы успешно вышли из аккаунта.\n\n" "Для повторной работы используйте /start"
    )
