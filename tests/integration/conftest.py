import time
import pytest
import socket
import asyncio
import uvicorn
from concurrent.futures.process import ProcessPoolExecutor
from multiprocessing import Process, Pool
from urllib.parse import urlparse


from source.main import create_app
from source.infrastructure.services.hh_service import HHService
from source.infrastructure.settings.test import TestAppSettings


@pytest.fixture()
def hh_service() -> HHService:
    return HHService()


@pytest.fixture()
def oauth_url(hh_service: HHService) -> str:
    return hh_service.get_auth_url("telegram")


@pytest.fixture(scope="session")
def test_settings() -> TestAppSettings:
    return TestAppSettings()


@pytest.fixture(scope="function")
def run_test_server(test_settings: TestAppSettings):
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
        yield
    finally:
        if proc.is_alive():
            proc.terminate()
        proc.join(timeout=5.0)
