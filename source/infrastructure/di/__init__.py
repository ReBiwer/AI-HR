from fastapi import FastAPI
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka

from source.infrastructure.di.providers import (
    ServicesProviders,
    UseCasesProviders,
)


def init_di_container(app: FastAPI) -> None:
    container = make_async_container(
        ServicesProviders(),
        UseCasesProviders(),
    )
    setup_dishka(container, app)
