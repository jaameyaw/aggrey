"""PostgresRepository against the seeded test database (see conftest.py)."""

from datetime import date, time

import psycopg
import pytest

from aggrey.adapters.repository import RepositoryError
from aggrey.domain.models import MealType, MenuScope, ScheduleType
from tests.integration.conftest import requires_database, with_repository

pytestmark = requires_database


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


def test_unreachable_database_raises_repository_error() -> None:
    dsn = "postgresql://aggrey_readonly:wrong@127.0.0.1:1/none"

    with pytest.raises(RepositoryError):
        with_repository(dsn, lambda r: r.get_metadata("timezone"), timeout_s=1)
