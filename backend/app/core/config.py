"""Configuration management."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MontGoWork"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./montgowork.db"
    credit_api_url: str = "http://localhost:8001"
    credit_api_key: str = "montgowork-dev"
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    brightdata_api_key: str = ""
    brightdata_dataset_id: str = ""

    # Logging
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env")

    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
