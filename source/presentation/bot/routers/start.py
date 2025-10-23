"""
Роутер для обработки команды /start.

Этот модуль обрабатывает начальную команду пользователя и процесс авторизации.

Логика работы:
1. Если пользователь приходит с payload (после авторизации) - сохраняем токены
2. Если пользователь уже авторизован - показываем главное меню
3. Если не авторизован - предлагаем авторизоваться
"""

import json
from aiogram.types import Message
from aiogram.dispatcher.router import Router
from aiogram.filters.command import CommandStart, CommandObject
from aiogram.utils.payload import decode_payload
from aiogram.fsm.context import FSMContext
from dishka import FromDishka

from source.application.services.hh_service import IHHService
from source.presentation.bot.utils.token_manager import TokenManager
from source.presentation.bot.schemas import TGUser


router = Router()


@router.message(CommandStart())
async def start(
    message: Message,
    state: FSMContext,
    hh_service: FromDishka[IHHService],
    command: CommandObject = None,
):
    """
    Обработчик команды /start.

    Args:
        message: Сообщение от пользователя
        state: FSM context для работы с данными пользователя
        hh_service: Сервис для работы с HH.ru API
        command: Объект команды с аргументами

    Почему используем FSMContext:
    - Автоматически привязывается к пользователю (user_id)
    - Данные сохраняются между сообщениями
    - Поддерживает различные backend'ы (Memory, Redis, MongoDB)
    - Асинхронный и быстрый
    """
    # Инициализируем менеджер токенов
    token_manager = TokenManager(state)

    # Проверяем, пришел ли пользователь после авторизации (с payload)
    args = command.args
    if args:
        try:
            # Декодируем payload, который пришел от backend после авторизации
            payload = json.loads(decode_payload(args))

            # Извлекаем данные токенов

            access_token = payload.get("access_token")
            refresh_token = payload.get("refresh_token")
            expires_in = payload.get("expires_in", 86400)  # По умолчанию 24 часа
            user_schema = TGUser.model_validate(payload, from_attributes=True)

            if access_token and refresh_token:
                # Сохраняем токены в storage
                await token_manager.save_tokens(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=expires_in,
                    user_info=user_schema.model_dump(),
                )

                await message.answer(
                    f"✅ Отлично, {user_schema.name}! Авторизация успешна.\n\n"
                    "Теперь вы можете использовать все функции бота.\n"
                    "Используйте /help для просмотра доступных команд."
                )
                return
            else:
                await message.answer(
                    "⚠️ Произошла ошибка при авторизации. Попробуйте еще раз."
                )
                # Очищаем возможные некорректные данные
                await token_manager.clear_tokens()

        except (json.JSONDecodeError, ValueError):
            await message.answer(
                "⚠️ Ошибка обработки данных авторизации. Попробуйте заново."
            )
            await token_manager.clear_tokens()
            return

    # Проверяем, авторизован ли пользователь уже
    is_authorized = await token_manager.is_token_valid()

    if is_authorized:
        # Пользователь уже авторизован, показываем главное меню
        user_info = await token_manager.get_user_info()

        await message.answer(
            f"👋 С возвращением, {user_info.name}!\n\n"
            "Вы уже авторизованы. Используйте /help для просмотра команд.\n\n"
            "Если хотите выйти, используйте /logout"
        )
    else:
        # Пользователь не авторизован, предлагаем пройти авторизацию
        auth_url = hh_service.get_auth_url("telegram")
        await message.answer(
            "👋 Добро пожаловать в бот для работы с HeadHunter!\n\n"
            "Для начала работы необходимо авторизоваться:\n"
            f"<a href='{auth_url}'>🔐 Авторизоваться в HH</a>\n\n"
            "После авторизации вы сможете:\n"
            "• Просматривать вакансии\n"
            "• Управлять откликами\n"
            "• Работать с резюме\n"
            "• И многое другое!",
        )
