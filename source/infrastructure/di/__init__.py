from fastapi import FastAPI
from aiogram import Dispatcher
from dishka import make_async_container, AsyncContainer
from dishka.integrations.fastapi import setup_dishka as fastapi_setup
from dishka.integrations.aiogram import setup_dishka as aiogram_setup, AiogramProvider

from source.infrastructure.di.providers import (
    ServicesProviders,
    UseCasesProviders,
    RepositoriesProviders,
)


def container_factory() -> AsyncContainer:
    return make_async_container(
        ServicesProviders(), UseCasesProviders(), RepositoriesProviders()
    )


def bot_container_factory() -> AsyncContainer:
    return make_async_container(
        ServicesProviders(),
        UseCasesProviders(),
        RepositoriesProviders(),
        AiogramProvider(),
    )


def init_di_container(app: FastAPI) -> None:
    fastapi_setup(container_factory(), app)


def init_di_container_bot(dp: Dispatcher) -> None:
    aiogram_setup(bot_container_factory(), router=dp, auto_inject=True)
