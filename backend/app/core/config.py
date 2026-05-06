"""Configuration management."""

import ipaddress
import logging
import re
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.db_url import infer_dialect

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
]

_CITY_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,49}$")


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
    openai_base_url: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Audit logging
    audit_log_path: str = ""
    audit_hash_salt: str = "montgowork-default-salt"

    brightdata_api_key: str = ""
    brightdata_dataset_id: str = ""
    brightdata_job_domains: str = "indeed.com"
    admin_api_key: str = ""

    # USAJobs API
    usajobs_api_key: str = ""
    usajobs_email: str = ""

    # City
    # Default flipped from "montgomery" → "fort-worth" since the
    # active reference deployment is Fort Worth (HackFW 2026). Both
    # configs still ship under cities/*.yaml — set CITY=montgomery
    # in the env to fall back to the legacy AL deployment.
    city: str = "fort-worth"

    # Data
    data_dir: str = ""

    # Proxy
    trusted_proxy_hosts: str = "127.0.0.1"

    # Logging
    log_level: str = "INFO"

    # CORS — Next.js dev server falls back to 3001/3002/3003 when earlier
    # ports are busy on the dev box. Allow the common range out of the box
    # so the demo works regardless of which port the dev server picked.
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003"

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("city")
    @classmethod
    def _validate_city_slug(cls, v: str) -> str:
        if not _CITY_SLUG_RE.match(v):
            raise ValueError(
                "city must be a lowercase slug (letters, digits, hyphens, "
                "starting with a letter, max 50 chars)"
            )
        return v

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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def db_dialect(self) -> str:
        """SQLAlchemy dialect inferred from ``database_url``.

        Returns ``"sqlite"`` or ``"postgresql"``. Used by
        ``app.core.database`` to pick a pool class and by test
        fixtures to skip postgres-specific axes when only sqlite is
        configured. Raises ``ValueError`` for unsupported schemes.
        """
        return infer_dialect(self.database_url)

    @model_validator(mode="after")
    def _validate_db_dialect_supported(self) -> "Settings":
        """Reject unsupported DATABASE_URL schemes at instantiation."""
        # Touching the property forces ``infer_dialect`` to run; if
        # the URL is mysql/oracle/etc, ValueError surfaces as a
        # Pydantic ValidationError rather than a runtime AttributeError.
        _ = self.db_dialect
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
