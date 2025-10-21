import datetime
import urllib.parse
from redis.asyncio.client import Redis

from source.infrastructure.services.new_hh_service import AuthConfig, TokenManager
from source.application.services.hh_service import AuthTokens


def test_auth_confi(auth_config):
    url = auth_config.get_full_url("/mine")
    assert auth_config.token_url == "https://api.hh.ru/token"
    assert auth_config.base_url == "https://api.hh.ru"
    assert url == "https://api.hh.ru/mine"

    url_with_params = auth_config.get_full_url("/mine", id=1, name="Vova")
    assert url_with_params == "https://api.hh.ru/mine?id=1&name=Vova"

    auth_url = auth_config.get_auth_url("test_state")
    auth_params = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": auth_config.client_id,
            "redirect_uri": auth_config.redirect_uri,
            "state": "test_state",
        }
    )
    assert auth_url == f"{auth_config.authorize_url}?{auth_params}"


async def test_token_manager(
    redis_client: Redis, tokens: AuthTokens, auth_config: AuthConfig
):
    manager = TokenManager(
        config=auth_config,
        redis_client=redis_client,
    )
    test_subject = "test_subject"
    await manager.save_tokens(test_subject, tokens)
    check = await manager.get_tokens(test_subject)
    assert check
    assert check["access_token"] == tokens["access_token"]
    assert check["refresh_token"] == tokens["refresh_token"]
    assert isinstance(check["expires_in"], int)
    assert isinstance(check["expire_at"], datetime.datetime)
