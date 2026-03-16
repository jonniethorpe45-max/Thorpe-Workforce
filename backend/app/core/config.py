import json
from functools import lru_cache
from typing import Annotated, List

from pydantic import field_validator, model_validator
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
    support_email: str = "support@thorpeworkforce.ai"
    google_client_id: str = ""
    google_client_secret: str = ""
    workspace_daily_send_cap: int = 250
    marketplace_platform_fee_percent: float = 0.30
    billing_provider: str = "placeholder"
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_pro_monthly: str = ""
    stripe_price_id_pro_annual: str = ""
    stripe_price_id_creator_monthly: str = ""
    stripe_price_id_creator_annual: str = ""
    stripe_price_id_enterprise_monthly: str = ""
    app_base_url: str = "http://localhost:3000"
    stripe_billing_portal_return_url: str = "http://localhost:3000/app/settings/billing"
    internal_worker_builder_enabled: bool = False
    internal_worker_builder_token: str = ""
    worker_creator_enabled: bool = False
    cors_origins: Annotated[List[str], NoDecode] = ["http://localhost:3000"]
    trusted_hosts: Annotated[List[str], NoDecode] = ["localhost", "127.0.0.1", "testserver"]
    password_reset_token_ttl_minutes: int = 60

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

    @field_validator("marketplace_platform_fee_percent")
    @classmethod
    def validate_marketplace_fee(cls, value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    @field_validator("app_base_url", "stripe_billing_portal_return_url")
    @classmethod
    def normalize_base_urls(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if normalized and not (normalized.startswith("http://") or normalized.startswith("https://")):
            raise ValueError("URL settings must start with http:// or https://")
        return normalized

    @field_validator("trusted_hosts", mode="before")
    @classmethod
    def split_hosts(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            return [part.strip() for part in raw.split(",") if part.strip()]
        return [part.strip() for part in value if part.strip()]

    @field_validator("environment")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"development", "staging", "production", "test"}
        if normalized not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str, info):
        environment = str((info.data or {}).get("environment", "development")).lower()
        if environment in {"production", "staging"} and value.strip() in {"", "change-me"}:
            raise ValueError("SECRET_KEY must be set to a secure value in production/staging")
        return value

    @model_validator(mode="after")
    def validate_required_prod_values(self):
        if self.environment not in {"production", "staging"}:
            return self
        required = {
            "DATABASE_URL": self.database_url,
            "REDIS_URL": self.redis_url,
            "APP_BASE_URL": self.app_base_url,
            "SUPPORT_EMAIL": self.support_email,
            "SECRET_KEY": self.secret_key,
        }
        missing = [key for key, value in required.items() if not str(value or "").strip()]
        if missing:
            raise ValueError(f"Missing required settings for {self.environment}: {', '.join(missing)}")
        if self.database_url == "postgresql+psycopg2://postgres:postgres@localhost:5432/thorpe_workforce":
            raise ValueError("DATABASE_URL must be explicitly configured for production/staging")
        if self.redis_url == "redis://localhost:6379/0":
            raise ValueError("REDIS_URL must be explicitly configured for production/staging")
        if self.app_base_url == "http://localhost:3000":
            raise ValueError("APP_BASE_URL must be explicitly configured for production/staging")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
