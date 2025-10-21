import pytest
import datetime
from redis.asyncio.client import Redis

from source.infrastructure.settings.test import test_app_settings
from source.infrastructure.services.new_hh_service import AuthConfig
from source.application.services.hh_service import AuthTokens


@pytest.fixture()
def tokens() -> AuthTokens:
    return AuthTokens(
        access_token="access_token",
        refresh_token="refresh_token",
        expires_in=100,
        expire_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=100),
    )


@pytest.fixture()
def auth_config() -> AuthConfig:
    return AuthConfig(
        client_id="1234",
        client_secret="secret",
        redirect_uri="https://loaclhos:8000",
        user_agent="User-Agent 007",
    )


@pytest.fixture()
def redis_client() -> Redis:
    return Redis(
        host=test_app_settings.REDIS_HOST,
        port=test_app_settings.REDIS_PORT,
        db=test_app_settings.REDIS_DB_NUM,
    )
