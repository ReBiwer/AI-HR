from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    # Настройки для работы с API hh.ru
    HH_CLIENT_ID: str
    HH_CLIENT_SECRET: str
    HH_REDIRECT_URI: str

    HH_FAKE_SUBJECT: str = 1

    model_config = SettingsConfigDict(env_file=f"/{BASE_DIR}/.env", extra="ignore")

    # @property
    # def db_url(self) -> str:
    #     return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:5432/{self.DB_NAME}"
    #
    # @property
    # def redis_url(self) -> str:
    #     return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

app_settings = AppSettings()
