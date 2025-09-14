from fastapi import Request
from aiogram import Bot
from aiogram.utils.deep_linking import create_deep_link

from source.application.services.generator_urls import IGeneratorRedirectURL
from source.infrastructure.settings.app import app_settings


class GeneratorRedirectURL(IGeneratorRedirectURL):


    async def telegram_url(self, state: str) -> str:
        bot = Bot(app_settings.BOT_TOKEN)
        return create_deep_link(
            (await bot.get_my_name()).name,
            link_type="start",
            payload=state
        )

    def backend_url(self, request: Request, state: str) -> str:
        return str(request.url_for(state))
