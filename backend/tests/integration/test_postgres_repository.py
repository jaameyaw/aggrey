"""PostgresRepository against a real Postgres loaded with db/schema.sql, seed.sql and
migration 001, queried as the read-only `aggrey_readonly` role.

TEST_DATABASE_URL must point at a disposable server as a superuser, for example a
local `postgres:16` container. The fixture creates and drops its own database, and
sets a random login password on the cluster-wide `aggrey_readonly` role, so never
point it at Supabase.
"""

import os
import secrets
import uuid
from collections.abc import Awaitable, Callable, Iterator
from datetime import date, time
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo
from pydantic import SecretStr

from aggrey.adapters.postgres import PostgresRepository, create_pool
from aggrey.adapters.repository import RepositoryError
from aggrey.config import Settings
from aggrey.domain.models import MealType, MenuScope, ScheduleType
from tests.conftest import run

ADMIN_URL = os.environ.get("TEST_DATABASE_URL", "")
DB_DIR = Path(__file__).resolve().parents[3] / "db"
SQL_FILES = ("schema.sql", "seed.sql", "migrations/001_readonly_role.sql")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not ADMIN_URL, reason="set TEST_DATABASE_URL to run integration tests"),
]


@pytest.fixture(scope="module")
def readonly_dsn() -> Iterator[str]:
    dbname = f"aggrey_it_{uuid.uuid4().hex[:8]}"
    password = secrets.token_urlsafe(18)
    with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    try:
        with psycopg.connect(make_conninfo(ADMIN_URL, dbname=dbname), autocommit=True) as conn:
            for name in SQL_FILES:
                conn.execute((DB_DIR / name).read_bytes())
            conn.execute(
                sql.SQL("ALTER ROLE aggrey_readonly WITH LOGIN PASSWORD {}").format(
                    sql.Literal(password)
                )
            )
        yield make_conninfo(ADMIN_URL, dbname=dbname, user="aggrey_readonly", password=password)
    finally:
        with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
            conn.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(dbname))
            )


def with_repository[T](
    dsn: str, action: Callable[[PostgresRepository], Awaitable[T]], *, timeout_s: float = 10
) -> T:
    async def go() -> T:
        settings = Settings(database_url=SecretStr(dsn), db_connect_timeout_s=timeout_s)
        pool = create_pool(settings)
        await pool.open(wait=False)
        try:
            repository = PostgresRepository(
                pool, statement_timeout_ms=settings.db_statement_timeout_ms
            )
            return await action(repository)
        finally:
            await pool.close()

    return run(go())


def test_readonly_role_sees_the_seeded_dataset(readonly_dsn: str) -> None:
    with psycopg.connect(readonly_dsn) as conn:
        counts = conn.execute(
            "SELECT (SELECT count(*) FROM menus), (SELECT count(*) FROM hours),"
            " (SELECT count(*) FROM holidays), (SELECT count(*) FROM metadata)"
        ).fetchone()

    assert counts == (227, 10, 11, 11)


def test_readonly_role_cannot_write(readonly_dsn: str) -> None:
    with psycopg.connect(readonly_dsn) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute("DELETE FROM metadata")


def test_metadata_timezone(readonly_dsn: str) -> None:
    assert with_repository(readonly_dsn, lambda r: r.get_metadata("timezone")) == (
        "America/New_York"
    )
    assert with_repository(readonly_dsn, lambda r: r.get_metadata("no_such_key")) is None


def test_overrides_cover_the_whole_holiday_range(readonly_dsn: str) -> None:
    [thanksgiving] = with_repository(readonly_dsn, lambda r: r.find_overrides(date(2026, 11, 25)))
    assert thanksgiving.name == "Thanksgiving Holiday"
    assert thanksgiving.schedule_type is ScheduleType.BREAK
    assert thanksgiving.end_date == date(2026, 11, 27)

    assert with_repository(readonly_dsn, lambda r: r.find_overrides(date(2026, 11, 27)))
    assert with_repository(readonly_dsn, lambda r: r.find_overrides(date(2026, 11, 24))) == []


def test_hours_lookup(readonly_dsn: str) -> None:
    lunch = with_repository(
        readonly_dsn, lambda r: r.get_hours(ScheduleType.WEEKDAY, MealType.LUNCH)
    )
    assert lunch is not None
    assert isinstance(lunch.start_time, time)
    assert lunch.start_time < lunch.end_time

    weekend_breakfast = with_repository(
        readonly_dsn, lambda r: r.get_hours(ScheduleType.WEEKEND, MealType.BREAKFAST)
    )
    assert weekend_breakfast is None


def test_weekly_menu_is_ordered_and_station_filter_ignores_case(readonly_dsn: str) -> None:
    breakfast = with_repository(
        readonly_dsn, lambda r: r.get_menu(MenuScope.WEEKLY, 1, MealType.BREAKFAST)
    )
    assert breakfast[0].food_item == "Scrambled Eggs"
    keys = [(item.station, item.display_order) for item in breakfast]
    assert keys == sorted(keys)

    filtered = with_repository(
        readonly_dsn,
        lambda r: r.get_menu(MenuScope.WEEKLY, 1, MealType.BREAKFAST, station=" BREAKFAST "),
    )
    assert filtered == [item for item in breakfast if item.station == "Breakfast"]


def test_holiday_sample_menu_has_brunch_and_dinner_without_weekday(readonly_dsn: str) -> None:
    brunch = with_repository(
        readonly_dsn, lambda r: r.get_menu(MenuScope.HOLIDAY_SAMPLE, None, MealType.BRUNCH)
    )
    dinner = with_repository(
        readonly_dsn, lambda r: r.get_menu(MenuScope.HOLIDAY_SAMPLE, None, MealType.DINNER)
    )
    for items in (brunch, dinner):
        assert items
        assert all(item.day_of_week is None for item in items)


def test_food_search_matches_substrings_and_escapes_wildcards(readonly_dsn: str) -> None:
    found = with_repository(
        readonly_dsn, lambda r: r.search_food("scrambled EGGS", MenuScope.WEEKLY, 1)
    )
    assert "Scrambled Eggs" in [item.food_item for item in found]

    assert with_repository(readonly_dsn, lambda r: r.search_food("%", MenuScope.WEEKLY, 1)) == []
    assert with_repository(readonly_dsn, lambda r: r.search_food("_", MenuScope.WEEKLY, 1)) == []


def test_unreachable_database_raises_repository_error() -> None:
    dsn = "postgresql://aggrey_readonly:wrong@127.0.0.1:1/none"

    with pytest.raises(RepositoryError):
        with_repository(dsn, lambda r: r.get_metadata("timezone"), timeout_s=1)
