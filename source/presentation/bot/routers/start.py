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

from source.application.repositories.base import IUnitOfWork
from source.application.repositories.user import IUserRepository
from source.application.services.hh_service import IHHService
from source.domain.entities.user import UserEntity
from source.infrastructure.services.hh_service import CustomTokenManager


router = Router()


@router.message(CommandStart())
async def start(
    message: Message,
    state: FSMContext,
    hh_service: FromDishka[IHHService],
    token_manager: FromDishka[CustomTokenManager],
    class_repo: FromDishka[type[IUserRepository]],
    uow: FromDishka[IUnitOfWork],
    command: CommandObject = None,
):
    """
    Обработчик команды /start.

    Args:
        message: Сообщение от пользователя
        state: FSM context для работы с данными пользователя
        hh_service: Сервис для работы с HH.ru API
        token_manager:
        class_repo:
        uow:
        command: Объект команды с аргументами

    Почему используем FSMContext:
    - Автоматически привязывается к пользователю (user_id)
    - Данные сохраняются между сообщениями
    - Поддерживает различные backend'ы (Memory, Redis, MongoDB)
    - Асинхронный и быстрый
    """
    # Проверяем, пришел ли пользователь после авторизации (с payload)
    args = command.args
    if args:
        try:
            payload = json.loads(decode_payload(args))
            hh_id_user: str = payload.get("hh_id")
            id_user: int = payload.get("id")
            access_token = await token_manager.ensure_access(hh_id_user)
            if access_token:
                async with uow as session:
                    user_repo = class_repo(session)
                    user: UserEntity = await user_repo.get(id=id_user)
                    user_tg_id = message.from_user.id
                    user.telegram_id = user_tg_id
                    await user_repo.update(user)

                await state.update_data({"hh_id": hh_id_user, "id": id_user})

                await message.answer(
                    f"✅ Отлично, {user.name}! Авторизация успешна.\n\n"
                    "Теперь вы можете использовать все функции бота.\n"
                    "Используйте /help для просмотра доступных команд."
                )
                return
            else:
                await message.answer(
                    "⚠️ Произошла ошибка при авторизации. Попробуйте еще раз."
                )
                # Очищаем возможные некорректные данные

        except (json.JSONDecodeError, ValueError):
            await message.answer(
                "⚠️ Ошибка обработки данных авторизации. Попробуйте заново."
            )
            return

    # Проверяем, авторизован ли пользователь уже
    data_state = await state.get_data()
    if "hh_id" in data_state and data_state["hh_id"]:
        # Пользователь уже авторизован, показываем главное меню
        id_user = data_state["id"]

        async with uow as session:
            user_repo = class_repo(session)
            user: UserEntity = await user_repo.get(id=id_user)

        await message.answer(
            f"👋 С возвращением, {user.name}!\n\n"
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
