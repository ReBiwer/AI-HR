from fastapi import FastAPI
from contextlib import asynccontextmanager

from source.presentation.api.auth import router as auth_router
from source.presentation.api.ai import router as ai_router
from source.infrastructure.settings.app import app_settings
from source.infrastructure.di import init_di_container
from source.presentation.wsgi import Application, get_app_options


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.dishka_container.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI-HR",
        description="Clean Architecture implementation for AI HR",
        lifespan=lifespan,
    )

    app.include_router(auth_router)
    app.include_router(ai_router)
    init_di_container(app)

    return app


if __name__ == "__main__":
    gunicorn_app = Application(
        app=create_app(),
        options=get_app_options(
            host=app_settings.BACKEND_HOST,
            port=app_settings.BACKEND_PORT,
            timeout=900,
            workers=4,
        ),
    )
    gunicorn_app.run()
