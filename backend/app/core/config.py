import json
from functools import lru_cache
from typing import Annotated, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    workspace_daily_send_cap: int = 250
    internal_worker_builder_enabled: bool = False
    internal_worker_builder_token: str = ""
    cors_origins: Annotated[List[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [str(part).strip() for part in parsed if str(part).strip()]
            if isinstance(parsed, str) and parsed.strip():
                return [parsed.strip()]
            return [part.strip() for part in raw.split(",") if part.strip()]
        return [part.strip() for part in value if part.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
