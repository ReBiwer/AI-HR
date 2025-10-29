"""
Модуль инициализации и запуска бота.

Этот модуль отвечает за:
- Настройку хранилища для FSM (Redis для production)
- Регистрацию роутеров и middleware
- Настройку команд бота
- Запуск polling

Почему именно такая структура:
- Разделение concerns (каждая часть отвечает за свое)
- Легко переключаться между dev и production окружениями
- Централизованная настройка бота
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from source.presentation.bot.middlewares import AuthMiddleware
from source.presentation.bot.routers import main_router
from source.infrastructure.settings.app import app_settings
from source.infrastructure.di import init_di_container_bot


async def set_commands(bot: Bot):
    """
    Устанавливает команды бота, видимые в меню Telegram.

    Почему это важно:
    - Пользователь видит доступные команды в меню
    - Автодополнение команд в клиенте Telegram
    - Улучшает UX
    """
    commands = [
        BotCommand(command="start", description="🚀 Старт / Авторизация"),
        BotCommand(command="help", description="❓ Помощь"),
        BotCommand(command="profile", description="👤 Мой профиль HH"),
        BotCommand(command="vacancies", description="💼 Поиск вакансий"),
        BotCommand(command="logout", description="🚪 Выход"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


def create_storage():
    """
    Создает хранилище для FSM в зависимости от окружения.

    Returns:
        BaseStorage: Экземпляр хранилища (Redis или Memory)

    Почему так:
    - В production используем Redis для персистентности данных
    - В dev можно использовать MemoryStorage для простоты
    - Легко переключаться через переменную окружения или настройки

    Важно:
    - RedisStorage хранит данные даже после перезапуска бота
    - MemoryStorage теряет данные при перезапуске
    - Redis обязателен для production, так как токены не должны теряться
    """
    # Проверяем, настроен ли Redis
    if app_settings.REDIS_HOST and app_settings.REDIS_PORT:
        # Production: используем Redis
        # Формируем URL для подключения к Redis
        # Используем отдельную базу данных для FSM (обычно отличную от checkpoint DB)
        redis_url = f"redis://{app_settings.REDIS_HOST}:{app_settings.REDIS_PORT}/0"

        storage = RedisStorage.from_url(
            redis_url,
            # Опционально: можно настроить префикс ключей
            # key_builder=lambda chat_id, user_id, destiny: f"fsm:{chat_id}:{user_id}:{destiny}"
        )
        print(f"✅ Используется RedisStorage: {redis_url}")
        return storage
    else:
        # Development: используем Memory (не рекомендуется для production!)
        print("⚠️ Используется MemoryStorage (данные будут потеряны при перезапуске)")
        return MemoryStorage()


async def run_bot():
    """
    Основная функция запуска бота.

    Порядок инициализации важен:
    1. Создаем bot и storage
    2. Создаем dispatcher с storage
    3. Регистрируем middleware (если есть)
    4. Подключаем роутеры
    5. Инициализируем DI контейнер
    6. Устанавливаем команды
    7. Запускаем polling
    """
    bot = Bot(
        token=app_settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Создаем хранилище
    storage = create_storage()

    # Создаем dispatcher с хранилищем
    dp = Dispatcher(storage=storage)

    # Удаляем webhook, если он был установлен ранее
    # Это важно при переключении с webhook на polling
    await bot.delete_webhook()

    # Подключаем роутеры
    # Порядок важен! Первые роутеры обрабатываются раньше
    dp.include_router(main_router)
    dp.message.middleware(AuthMiddleware())
    # Инициализируем DI контейнер (dishka)
    # Это позволяет инжектировать зависимости в handlers
    init_di_container_bot(dp)

    # Устанавливаем команды бота
    await set_commands(bot)

    # Запускаем polling
    # skip_updates=True - пропускаем сообщения, которые пришли пока бот был оффлайн
    print("🤖 Бот запущен и готов к работе!")
    await dp.start_polling(bot)
