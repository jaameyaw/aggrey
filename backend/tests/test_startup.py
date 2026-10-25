from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from aggrey.adapters.fake import FakeRepository
from aggrey.adapters.repository import RepositoryError
from aggrey.app import StartupError, create_app, load_timezone
from aggrey.config import Settings
from tests.conftest import run


class UnreachableRepository(FakeRepository):
    async def get_metadata(self, key: str) -> str | None:
        raise RepositoryError("dining data is unavailable")


def test_valid_timezone_is_loaded() -> None:
    repository = FakeRepository(metadata={"timezone": "America/New_York"})

    assert run(load_timezone(repository)) == ZoneInfo("America/New_York")


def test_missing_timezone_fails_clearly() -> None:
    with pytest.raises(StartupError, match=r"metadata\.timezone is missing"):
        run(load_timezone(FakeRepository()))


@pytest.mark.parametrize("value", ["Mars/Olympus_Mons", "../etc/passwd", "   "])
def test_invalid_timezone_fails_clearly(value: str) -> None:
    repository = FakeRepository(metadata={"timezone": value})

    with pytest.raises(StartupError, match=r"metadata\.timezone"):
        run(load_timezone(repository))


def test_unreadable_database_fails_clearly() -> None:
    with pytest.raises(StartupError, match=r"Could not read metadata\.timezone"):
        run(load_timezone(UnreachableRepository()))


def test_app_refuses_to_start_without_timezone(settings: Settings) -> None:
    app = create_app(settings, FakeRepository())

    with pytest.raises(StartupError), TestClient(app):
        pass


def test_app_exposes_timezone_after_startup(settings: Settings) -> None:
    app = create_app(settings, FakeRepository(metadata={"timezone": "America/New_York"}))

    with TestClient(app):
        assert app.state.timezone == ZoneInfo("America/New_York")
