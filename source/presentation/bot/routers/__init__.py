"""
Главный роутер бота, объединяющий все дочерние роутеры.

Порядок подключения роутеров важен - они обрабатываются последовательно.
"""

from aiogram import Router
from .start import router as start_router
from .help import router as help_router
from .profile import router as profile_router

main_router = Router()

# Подключаем роутеры в порядке приоритета
main_router.include_routers(
    start_router,
    help_router,
    profile_router,
)
