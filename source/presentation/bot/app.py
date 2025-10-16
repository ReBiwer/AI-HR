from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi.requests import Request
from fastapi import FastAPI, APIRouter


router = APIRouter()


@router.post("/webhook")
async def webhook(request: Request) -> None:
    """
    Ручка для обработки вебхуков от телеграмма
    Принцип действия: принимает запрос request,
    валидирует содержимое запроса в объект Update и добавляет в контекст экземпляр бота,
    передает этот объект в диспетчер для дальнейшей обработки внутри телеграмм бота уже
    :param request:
    :return:
    """
    bot = request.app.state.bot
    dp = request.app.state.dp
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)


def get_bot_app(bot: Bot, dp: Dispatcher) -> FastAPI:
    app = FastAPI()
    app.state.bot = bot
    app.state.dp = dp
    app.include_router(router)
    return app
