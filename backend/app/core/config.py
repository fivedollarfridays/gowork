"""Configuration management."""

import ipaddress
import logging
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

    # Multi-provider LLM
    llm_provider: str = "anthropic"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Audit logging
    audit_log_path: str = ""
    audit_hash_salt: str = "montgowork-default-salt"

    brightdata_api_key: str = ""
    brightdata_dataset_id: str = ""
    admin_api_key: str = ""

    # JSearch (RapidAPI)
    jsearch_api_key: str = ""
    jsearch_host: str = "jsearch.p.rapidapi.com"

    # Data
    data_dir: str = ""

    # Proxy
    trusted_proxy_hosts: str = "127.0.0.1"

    # Logging
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

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

    @model_validator(mode="after")
    def _reject_default_salt_in_production(self) -> "Settings":
        """HIGH-3 / LOW-4: Weak default audit hash salt must not reach production."""
        if self.audit_hash_salt == "montgowork-default-salt":
            if self.environment == "production":
                raise ValueError(
                    "audit_hash_salt must be changed from the default value "
                    "in production — set AUDIT_HASH_SALT env var"
                )
            if self.environment not in ("development", "test"):
                logging.getLogger(__name__).warning(
                    "audit_hash_salt is set to the default value — "
                    "set AUDIT_HASH_SALT for non-development environments"
                )
        return self

    @model_validator(mode="after")
    def _reject_weak_admin_key_in_production(self) -> "Settings":
        """MED-6: Admin API key must be >= 32 chars in production."""
        if self.environment != "production":
            return self
        if len(self.admin_api_key) < 32:
            raise ValueError(
                "admin_api_key must be at least 32 characters in production "
                "— set ADMIN_API_KEY env var"
            )
        return self

    @model_validator(mode="after")
    def _reject_localhost_cors_in_production(self) -> "Settings":
        """Reject localhost CORS origins in production."""
        if self.environment != "production":
            return self
        if "localhost" in self.cors_origins:
            raise ValueError(
                "cors_origins must not contain localhost in production "
                "— set CORS_ORIGINS env var to production domains"
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
