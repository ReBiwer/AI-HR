from typing import Mapping, Any
from fastapi import Request
from aiogram import Bot
from aiogram.utils.deep_linking import create_deep_link

from source.application.services.state_manager import IStateManager, URL
from source.infrastructure.settings.app import app_settings
from source.infrastructure.utils.jwt import encode_jwt


class StateManager(IStateManager):

    async def state_convert(self, state, payload: Mapping[str, Any], request: Request) -> URL:
        encoded_payload = encode_jwt(payload, app_settings.JWT_TOKEN)
        if state == "telegram":
            username_bot = (await Bot(app_settings.BOT_TOKEN).get_me()).username
            bot_link = create_deep_link(username_bot, link_type="start", payload=encoded_payload)
            return bot_link

        redirect_link = request.url_for(state, payload=encoded_payload)
        return redirect_link.path
