from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    scoutai_cors_origins: str = "http://localhost:3000"
    scoutai_demo_mode: str = "auto"  # auto | always | never

    @property
    def demo_mode(self) -> bool:
        mode = (self.scoutai_demo_mode or "auto").lower()
        if mode == "always":
            return True
        if mode == "never":
            return False
        return not bool(self.openai_api_key.strip())

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.scoutai_cors_origins.split(",") if o.strip()]


settings = Settings()
