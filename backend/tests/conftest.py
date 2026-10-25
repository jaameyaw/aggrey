import asyncio
from collections.abc import Coroutine, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from aggrey.adapters.fake import FakeRepository
from aggrey.app import create_app
from aggrey.config import Settings

_SETTINGS_ENV = (
    "DATABASE_URL",
    "DB_CONNECT_TIMEOUT_S",
    "DB_STATEMENT_TIMEOUT_MS",
    "DB_POOL_MIN_SIZE",
    "DB_POOL_MAX_SIZE",
    "LOG_LEVEL",
    "APP_ENV",
)


def run[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine on a selector loop; psycopg async rejects Windows' Proactor loop."""
    return asyncio.run(coro, loop_factory=asyncio.SelectorEventLoop)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """No settings from the developer's shell or backend/.env."""
    for name in _SETTINGS_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url=SecretStr("postgresql://unused@localhost/unused"), app_env="test")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    repository = FakeRepository(metadata={"timezone": "America/New_York"})
    with TestClient(create_app(settings, repository)) as test_client:
        yield test_client
