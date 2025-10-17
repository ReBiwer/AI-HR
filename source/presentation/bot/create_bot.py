from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from source.presentation.bot.routers import main_router
from source.infrastructure.settings.app import app_settings
from source.infrastructure.di import init_di_container_bot


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Старт"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def run_bot():
    bot = Bot(
        token=app_settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    await bot.delete_webhook()
    dp.include_router(main_router)
    init_di_container_bot(dp)

    await set_commands(bot)
    await dp.start_polling(bot)
