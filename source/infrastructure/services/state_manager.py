from fastapi import Request
from aiogram import Bot
from aiogram.utils.deep_linking import create_deep_link

from source.application.services.state_manager import IStateManager, URL
from source.infrastructure.settings.app import app_settings


class StateManager(IStateManager):

    async def state_converter(self, state, request: Request) -> URL:
        if state == "telegram":
            name_bot = str(await Bot(app_settings.BOT_TOKEN).get_my_name())
            bot_link = create_deep_link(name_bot, link_type="start", payload="redirect")
            return bot_link

        redirect_link = request.url_for(state)
        return redirect_link.path
