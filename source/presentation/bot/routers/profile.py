from typing import Union

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from dishka import FromDishka

from source.constants.texts_message import ProfileMessages
from source.constants.storage_keys import StorageKeys, CallbackKeys
from source.presentation.bot.keyboards.inline import resumes_keyboard, ResumeCallback
from source.domain.entities.user import UserEntity

router = Router()


@router.message(Command("profile"))
@router.callback_query(F.data == CallbackKeys.PROFILE)
async def show_profile(
    message: Union[Message, CallbackQuery],
    state: FSMContext,
    user: FromDishka[Union[UserEntity | None]],
):
    """
    Показывает информацию о пользователе
    """
    try:
        if user is None:
            raise PermissionError("Необходимо авторизоваться")
        active_resume_title = await state.get_value(StorageKeys.ACTIVE_RESUME_TITLE)
        text_message = ProfileMessages.profile_base(user, active_resume_title)
        if isinstance(message, Message):
            await message.answer(
                text_message, reply_markup=resumes_keyboard(user.resumes)
            )
            return
        await message.answer()
        await message.message.answer(
            text_message, reply_markup=resumes_keyboard(user.resumes)
        )
    except PermissionError as e:
        await message.answer(f"{str(e)}\n" "Перейдите в начало для авторизации: /start")
    except Exception as e:
        await message.answer(
            f"⚠️ Ошибка при получении профиля: {str(e)}\n"
            "Попробуйте авторизоваться заново: /start"
        )


@router.callback_query(ResumeCallback.filter(F.action == "active"))
async def select_active_resume(
    callback: CallbackQuery,
    callback_data: ResumeCallback,
    state: FSMContext,
    user: FromDishka[Union[UserEntity, None]],
):
    await state.update_data(
        {
            StorageKeys.ACTIVE_RESUME_ID: callback_data.resume_id,
            StorageKeys.ACTIVE_RESUME_TITLE: callback_data.title,
        }
    )
    await callback.message.edit_text(
        ProfileMessages.profile_base(user, callback_data.title),
        reply_markup=resumes_keyboard(user.resumes, callback_data.resume_id),
    )
    await callback.answer()


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
