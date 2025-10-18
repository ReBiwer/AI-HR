import json
from aiogram.types import Message
from aiogram.dispatcher.router import Router
from aiogram.filters.command import CommandStart, CommandObject
from aiogram.utils.payload import decode_payload
from dishka import FromDishka

from source.application.services.hh_service import IHHService


router = Router()


@router.message(CommandStart())
async def start(
    message: Message,
    hh_service: FromDishka[IHHService],
    command: CommandObject = None,
):
    args = command.args
    if args:
        payload = json.loads(decode_payload(args))
        await message.answer(f"Приятно познакомиться {payload["name"]}")
        return
    auth_url = hh_service.get_auth_url("telegram")
    await message.answer(
        f"Добрый день, перед началом работы нужно <a href='{auth_url}'>авторизоваться</a> в HH",
    )
