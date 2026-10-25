"""Application settings, read from environment variables (or `backend/.env`) at startup."""

from typing import Literal, Self

from pydantic import Field, SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(Exception):
    """Configuration is missing or invalid. The message names variables, never values."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Postgres connection string for the read-only `aggrey_readonly` role (N-33, ADR 0001).
    database_url: SecretStr
    db_connect_timeout_s: float = Field(default=5.0, gt=0, le=60)
    db_statement_timeout_ms: int = Field(default=5000, gt=0, le=60000)
    db_pool_min_size: int = Field(default=1, ge=0)
    db_pool_max_size: int = Field(default=5, ge=1)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    app_env: Literal["development", "test", "production"] = "development"

    @model_validator(mode="after")
    def _pool_sizes(self) -> Self:
        if self.db_pool_min_size > self.db_pool_max_size:
            raise ValueError("DB_POOL_MIN_SIZE must not exceed DB_POOL_MAX_SIZE")
        return self


def load_settings() -> Settings:
    """Load settings, or raise ConfigError listing every bad variable by name."""
    try:
        return Settings()
    except ValidationError as exc:
        problems = []
        for error in exc.errors(include_input=False, include_url=False):
            name = "_".join(str(part) for part in error["loc"]).upper() or "SETTINGS"
            problems.append(f"{name}: {error['msg']}")
        raise ConfigError("Invalid configuration:\n  " + "\n  ".join(problems)) from None
