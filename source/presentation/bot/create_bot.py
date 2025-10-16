import asyncio
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from source.presentation.bot.app import get_bot_app
from source.presentation.bot.routers import main_router
from source.infrastructure.settings.app import app_settings
from source.infrastructure.di import init_di_container_bot


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Старт"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def on_startup(bot: Bot, dp: Dispatcher):
    await bot.set_webhook(
        url=f"{app_settings.WEBHOOK_URL}{app_settings.WEBHOOK_PATH}",
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()


async def create_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=app_settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_router(main_router)
    init_di_container_bot(dp)

    await set_commands(bot)
    return bot, dp


def create_bot_app() -> FastAPI:
    """
    Функция для создания приложения для обработки вебхуков телеграмм бота
    :return:
    """
    bot, dp = asyncio.run(create_bot())
    bot_app = get_bot_app(bot, dp)
    return bot_app
