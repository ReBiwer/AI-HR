import re
import json
import time
import pytest
import socket
import uvicorn
from urllib.parse import urlparse
from multiprocessing import Process
from playwright.async_api import Page
from hh_api.auth.token_manager import OAuthConfig

from source.main import create_app
from source.infrastructure.services.hh_service import HHService
from source.infrastructure.settings.test import TestAppSettings
from source.application.services.hh_service import AuthTokens


@pytest.fixture()
def hh_service(test_settings: TestAppSettings) -> HHService:
    service = HHService()
    service._hh_tm.config = OAuthConfig(
        client_id=test_settings.HH_CLIENT_ID,
        client_secret=test_settings.HH_CLIENT_SECRET,
        redirect_uri=test_settings.HH_REDIRECT_URI,
    )
    return service


@pytest.fixture()
def mock_hh_service(hh_service: HHService, mocker):
    mocker.patch(
        "source.infrastructure.di.providers.HHService",
        return_value=hh_service
    )

@pytest.fixture()
def oauth_url(hh_service: HHService, test_settings: TestAppSettings) -> str:
    return hh_service.get_auth_url("test_tokens")


@pytest.fixture(scope="session")
def test_settings() -> TestAppSettings:
    return TestAppSettings()


@pytest.fixture(scope="function")
def run_test_server(test_settings: TestAppSettings, mock_hh_service):
    parsed = urlparse(test_settings.HH_REDIRECT_URI)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8000

    def _serve(h: str, p: int) -> None:
        # создаём приложение внутри процесса и запускаем uvicorn
        app = create_app()
        uvicorn.run(app, host=h, port=p, log_level="warning", lifespan="on")

    proc = Process(target=_serve, args=(host, port), daemon=True)
    proc.start()

    # ждём доступности порта
    deadline = time.time() + 15.0
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                if s.connect_ex((host, port)) == 0:
                    break
            except OSError:
                pass
        time.sleep(0.1)
    else:
        # если не поднялся — завершаем процесс и падаем
        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=3.0)
        raise RuntimeError(f"Server did not start on {host}:{port} within 15s")

    try:
        print("сервер запущен")
        yield
    finally:
        if proc.is_alive():
            proc.terminate()
        proc.join(timeout=5.0)


@pytest.fixture()
async def auth_tokens(page: Page, oauth_url: str, test_settings: TestAppSettings, run_test_server):
    await page.goto(oauth_url)
    await page.get_by_label("Электронная почта или телефон").fill(test_settings.HH_LOGIN)
    await page.get_by_role("button", name="Войти с паролем").click()
    await page.get_by_label("Пароль").fill(test_settings.HH_PASSWORD)
    await page.get_by_role("button", name="Войти").first.click()
    pattern = re.compile(
        r"^http://localhost:8000/auth/hh/tokens/test\?(?=.*\bcode=[^&]+)(?=.*\bstate=test_tokens).+"
    )
    await page.wait_for_url(pattern)
    text = await page.text_content("pre, body")
    data = json.loads(text)
    return AuthTokens(access_token=data["access_token"], refresh_token=data["refresh_token"])
