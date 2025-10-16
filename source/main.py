from fastapi import FastAPI
from contextlib import asynccontextmanager

from source.presentation.api.auth import router as auth_router
from source.presentation.api.ai import router as ai_router
from source.infrastructure.settings.app import app_settings
from source.infrastructure.di import init_di_container
from source.presentation.wsgi import Application, get_app_options
from source.presentation.bot.create_bot import create_bot_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.dishka_container.close()


def create_web_app() -> FastAPI:
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
    import argparse

    parser = argparse.ArgumentParser(description="Какое приложение запускать")
    parser.add_argument(
        "--type-app",
        type=str,
        choices=("telegram", "web"),
        default="telegram",
        help="Какое приложение запустить",
    )
    args = parser.parse_args()

    if args.type_app == "telegram":
        app = create_bot_app()
        options = get_app_options(
            host=app_settings.BOT_APP_HOST,
            port=app_settings.BOT_APP_PORT,
            timeout=900,
            workers=4,
        )
    else:
        app = create_web_app()
        options = get_app_options(
            host=app_settings.BACKEND_HOST,
            port=app_settings.BACKEND_PORT,
            timeout=900,
            workers=4,
        )

    gunicorn_app = Application(
        app=app,
        options=options,
    )
    gunicorn_app.run()
