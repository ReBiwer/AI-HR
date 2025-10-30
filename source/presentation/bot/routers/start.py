import json
from typing import Union

from aiogram.types import Message
from aiogram.dispatcher.router import Router
from aiogram.filters.command import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from dishka import FromDishka

from source.application.use_cases.bot.authorization import AuthUseCase
from source.presentation.bot.keyboards.inline import profile_keyboard
from source.constants.storage_keys import StorageKeys
from source.application.services.hh_service import IHHService
from source.domain.entities.user import UserEntity


router = Router()


@router.message(CommandStart())
async def start(
    message: Message,
    state: FSMContext,
    hh_service: FromDishka[IHHService],
    auth_use_case: FromDishka[AuthUseCase],
    user: FromDishka[Union[UserEntity | None]],
    command: CommandObject = None,
):
    """
    Обработчик команды /start.

    Args:
        message: Сообщение от пользователя
        state: FSM context для работы с данными пользователя
        hh_service: Сервис для работы с HH.ru API
        auth_use_case: Use case авторизации
        user: Если не None пользователь авторизован
        command: Объект команды с аргументами
    """
    # Проверяем, пришел ли пользователь после авторизации (с payload)
    args = command.args
    if args:
        try:
            user = await auth_use_case(payload_str=args, tg_id=message.from_user.id)
            await state.update_data(
                {StorageKeys.USER_INFO: user.model_dump_json(exclude_unset=True)}
            )

            await message.answer(
                f"✅ Отлично, {user.name}! Авторизация успешна.\n\n"
                "Теперь вы можете использовать все функции бота.\n"
                "Используйте /help для просмотра доступных команд.",
                reply_markup=profile_keyboard(),
            )
        except (json.JSONDecodeError, ValueError):
            await message.answer(
                "⚠️ Ошибка обработки данных авторизации. Попробуйте заново."
            )
    else:
        if user:
            # Если пользователь есть, то приветствуем его
            await message.answer(
                f"👋 С возвращением, {user.name}!\n\n"
                "Вы уже авторизованы. Используйте /help для просмотра команд.\n\n",
                reply_markup=profile_keyboard(),
            )
        else:
            # Пользователь не авторизован, предлагаем пройти авторизацию
            auth_url = hh_service.get_auth_url("telegram")
            await message.answer(
                "👋 Добро пожаловать в бот для работы с HeadHunter!\n\n"
                "Для начала работы необходимо авторизоваться:\n"
                f"<a href='{auth_url}'>🔐 Авторизоваться в HH</a>\n\n"
                "После авторизации вы сможете:\n"
                "• Генерировать отклики на вакансии\n"
                "• Просматривать резюме (в разработке)\n"
                "• Просматривать вакансии (в разработке)\n"
                "• Управлять откликами (в разработке)\n"
                "• Работать с резюме (в разработке)\n"
                "• И многое другое!",
            )
