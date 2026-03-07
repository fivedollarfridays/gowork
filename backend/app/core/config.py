"""Configuration management."""

import ipaddress
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
]


class Settings(BaseSettings):
    app_name: str = "MontGoWork"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./montgowork.db"
    credit_api_url: str = "http://localhost:8001"
    credit_api_key: str = ""
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    brightdata_api_key: str = ""
    brightdata_dataset_id: str = ""
    admin_api_key: str = ""

    # Data
    data_dir: str = ""

    # Proxy
    trusted_proxy_hosts: str = "127.0.0.1"

    # Logging
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env")

    @model_validator(mode="after")
    def _reject_private_credit_url_in_production(self) -> "Settings":
        if self.environment != "production" or not self.credit_api_url:
            return self
        parsed = urlparse(self.credit_api_url)
        hostname = parsed.hostname or ""
        try:
            addr = ipaddress.ip_address(hostname)
        except ValueError:
            return self  # hostname (e.g. credit-api.example.com) — OK
        for net in _BLOCKED_NETWORKS:
            if addr in net:
                raise ValueError(
                    f"credit_api_url must not use private/link-local IP in production: {hostname}"
                )
        return self

    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
