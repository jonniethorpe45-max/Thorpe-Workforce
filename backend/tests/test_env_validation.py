import pytest

from app.core.config import Settings


def test_staging_requires_core_environment_values():
    with pytest.raises(Exception):
        Settings(
            environment="staging",
            secret_key="staging-secret",
            database_url="",
            redis_url="redis://localhost:6379/0",
            app_base_url="https://staging.thorpe.example",
            support_email="support@thorpe.example",
        )

    with pytest.raises(Exception):
        Settings(
            environment="production",
            secret_key="prod-secret",
            database_url="postgresql+psycopg2://user:pass@db:5432/app",
            redis_url="",
            app_base_url="https://app.thorpe.example",
            support_email="support@thorpe.example",
        )

    with pytest.raises(Exception):
        Settings(
            environment="production",
            secret_key="prod-secret",
            database_url="postgresql+psycopg2://postgres:postgres@localhost:5432/thorpe_workforce",
            redis_url="redis://localhost:6379/0",
            app_base_url="http://localhost:3000",
            support_email="support@thorpe.example",
        )


def test_staging_with_required_values_is_valid():
    cfg = Settings(
        environment="staging",
        secret_key="staging-secret",
        database_url="postgresql+psycopg2://user:pass@db:5432/app",
        redis_url="redis://redis:6379/0",
        app_base_url="https://staging.thorpe.example",
        support_email="support@thorpe.example",
    )
    assert cfg.environment == "staging"


def test_url_settings_require_http_or_https():
    with pytest.raises(Exception):
        Settings(app_base_url="ftp://example.com")
