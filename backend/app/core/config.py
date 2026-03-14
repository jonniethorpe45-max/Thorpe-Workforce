from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "Thorpe Workforce API"
    environment: str = "development"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 120
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/thorpe_workforce"
    redis_url: str = "redis://localhost:6379/0"
    ai_provider: str = "mock"
    email_provider: str = "mock"
    calendar_provider: str = "google"
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "sales@thorpeworkforce.com"
    google_client_id: str = ""
    google_client_secret: str = ""
    cors_origins: List[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
