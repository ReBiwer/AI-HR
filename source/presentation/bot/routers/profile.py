from typing import Union

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from dishka import FromDishka

from source.constants.storage_keys import StorageKeys, CallbackKeys
from source.presentation.bot.utils.formatter_messages import profile_text
from source.domain.entities.user import UserEntity

router = Router()


@router.message(Command("profile"))
@router.callback_query(F.data == CallbackKeys.PROFILE)
async def show_profile(
    message: Union[Message, CallbackQuery],
    user: FromDishka[UserEntity],
):
    """
    Показывает информацию о пользователе
    """
    text_message = profile_text(user)
    try:
        if isinstance(message, Message):
            await message.answer(text_message)
            return
        await message.answer()
        await message.message.answer(text_message)
    except Exception as e:
        await message.answer(
            f"⚠️ Ошибка при получении профиля: {str(e)}\n"
            "Попробуйте авторизоваться заново: /start"
        )


@router.message(Command("logout"))
@router.callback_query(F.data == CallbackKeys.LOGOUT)
async def logout(message: Union[Message, CallbackQuery], state: FSMContext):
    """
    Выход из аккаунта (очистка информации о пользователе их FSMContext).
    """
    await state.set_data({StorageKeys.USER_INFO: None})
    text_message = (
        "👋 Вы успешно вышли из аккаунта.\n\n" "Для повторной работы используйте /start"
    )
    if isinstance(message, Message):
        await message.answer(text_message)
        return
    await message.answer()
    await message.message.answer(text_message)
