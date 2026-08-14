from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", enable_decoding=False)

    app_env: str = "development"
    ahara_mode: str = "live"
    places_provider: str = "foursquare"
    foursquare_api_key: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_version: str = "0.1.0"
    database_url: str
    redis_url: str
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
