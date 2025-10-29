from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from dishka import FromDishka

from source.presentation.bot.storage_keys import StorageKeys
from source.presentation.bot.utils.splitter import split_long_message
from source.domain.entities.user import UserEntity

router = Router()


@router.message(Command("profile"))
async def show_profile(
    message: Message,
    user: FromDishka[UserEntity],
):
    """
    Показывает информацию о пользователе
    """

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


@router.message(Command("logout"))
async def logout(message: Message, state: FSMContext):
    """
    Выход из аккаунта (очистка информации о пользователе их FSMContext).
    """
    await state.set_data({StorageKeys.USER_INFO: None})

    await message.answer(
        "👋 Вы успешно вышли из аккаунта.\n\n" "Для повторной работы используйте /start"
    )
