from fastapi import FastAPI
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka

from source.infrastructure.di.providers import (
    ServicesProviders,
    UseCasesProviders,
    RepositoriesProviders,
)


def init_di_container(app: FastAPI) -> None:
    container = make_async_container(
        ServicesProviders(),
        UseCasesProviders(),
        RepositoriesProviders()
    )
    setup_dishka(container, app)
