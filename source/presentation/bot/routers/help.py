"""
Роутер для команды помощи.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("help"))
async def show_help(message: Message):
    """Показывает справку по командам бота."""
    help_text = """
        📚 <b>Справка по командам бота</b>

        <b>Основные команды:</b>
        /start - Начать работу / Авторизация в HH.ru
        /help - Показать эту справку
        /profile - Показать ваш профиль HH.ru
        /logout - Выйти из аккаунта

        <b>Работа с вакансиями:</b>
        /vacancies - Поиск вакансий (в разработке)

        <b>О боте:</b>
        Этот бот помогает управлять вашими откликами на вакансии
        через платформу HeadHunter.

        <b>Вопросы и поддержка:</b>
        Если у вас возникли проблемы, попробуйте:
        1. Выйти из аккаунта: /logout
        2. Авторизоваться заново: /start

        <b>Безопасность:</b>
        🔒 Ваши токены хранятся в защищенном хранилище Redis
        🔒 Токены автоматически очищаются при выходе
        🔒 Токены истекают через 24 часа (настраивается)
    """
    await message.answer(help_text)
