from aiogram.types import Message
from aiogram.dispatcher.router import Router
from aiogram.filters.command import CommandStart
from dishka import FromDishka

from source.application.services.hh_service import IHHService


router = Router()


@router.message(CommandStart)
async def start(
    message: Message,
    # command: CommandObject,
    hh_service: FromDishka[IHHService],
):
    # args = command.args
    # if args:
    #     payload = decode_payload(args)
    #     print(payload)
    #     return
    auth_url = hh_service.get_auth_url("telegram")
    await message.answer(
        f"Добрый день, перед началом работы нужно <a href='{auth_url}'>авторизоваться</a> в HH",
    )
