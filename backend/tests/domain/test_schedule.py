from datetime import date

import pytest

from aggrey.adapters.fake import FakeRepository
from aggrey.domain.models import HolidayPeriod, ScheduleType
from aggrey.domain.schedule import (
    DaySchedule,
    ScheduleDataError,
    load_schedule,
    resolve_schedule,
)
from tests.conftest import run
from tests.domain.seed import repository

THANKSGIVING = HolidayPeriod(
    "Thanksgiving Holiday",
    date(2026, 11, 25),
    date(2026, 11, 27),
    ScheduleType.BREAK,
    "calendar_date; user_confirmed_hours",
    "Sample holiday brunch menu.",
)


def test_weekday() -> None:
    assert resolve_schedule(date(2026, 10, 26), []) == DaySchedule(
        date(2026, 10, 26), ScheduleType.WEEKDAY
    )


@pytest.mark.parametrize("day", [date(2026, 10, 31), date(2026, 11, 1)])
def test_saturday_and_sunday_are_weekend(day: date) -> None:
    assert resolve_schedule(day, []).schedule_type == ScheduleType.WEEKEND


def test_override_beats_weekday_and_keeps_its_details() -> None:
    result = resolve_schedule(date(2026, 11, 25), [THANKSGIVING])
    assert result == DaySchedule(date(2026, 11, 25), ScheduleType.BREAK, THANKSGIVING)
    assert result.override is not None
    assert result.override.verification_status == "calendar_date; user_confirmed_hours"
    assert result.override.notes == "Sample holiday brunch menu."


def test_override_beats_weekend() -> None:
    # Saturday 2026-11-28 is outside the range; Friday 2026-11-27 is its last day.
    assert resolve_schedule(date(2026, 11, 27), [THANKSGIVING]).schedule_type == ScheduleType.BREAK
    saturday_break = HolidayPeriod(
        "Break", date(2026, 11, 28), date(2026, 11, 29), ScheduleType.BREAK, "x", None
    )
    assert (
        resolve_schedule(date(2026, 11, 28), [saturday_break]).schedule_type == ScheduleType.BREAK
    )


def test_more_than_one_override_is_a_data_error() -> None:
    other = HolidayPeriod(
        "Other", date(2026, 11, 25), date(2026, 11, 25), ScheduleType.HOLIDAY, "x", None
    )
    with pytest.raises(ScheduleDataError, match="more than one"):
        resolve_schedule(date(2026, 11, 25), [THANKSGIVING, other])


@pytest.mark.parametrize("kind", [ScheduleType.WEEKDAY, ScheduleType.WEEKEND])
def test_override_with_a_regular_schedule_type_is_a_data_error(kind: ScheduleType) -> None:
    bad = HolidayPeriod("Bad", date(2026, 11, 25), date(2026, 11, 25), kind, "x", None)
    with pytest.raises(ScheduleDataError, match="schedule type"):
        resolve_schedule(date(2026, 11, 25), [bad])


def test_override_that_does_not_cover_the_day_is_a_data_error() -> None:
    with pytest.raises(ScheduleDataError, match="does not cover"):
        resolve_schedule(date(2026, 11, 28), [THANKSGIVING])


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 11, 24), ScheduleType.WEEKDAY),
        (date(2026, 11, 25), ScheduleType.BREAK),  # first day, inclusive
        (date(2026, 11, 27), ScheduleType.BREAK),  # last day, inclusive
        (date(2026, 11, 28), ScheduleType.WEEKEND),
        (date(2026, 9, 7), ScheduleType.HOLIDAY),
        (date(2026, 12, 12), ScheduleType.BREAK),  # Saturday inside the exams period
    ],
)
def test_load_schedule_from_the_repository(day: date, expected: ScheduleType) -> None:
    assert run(load_schedule(day, repository())).schedule_type == expected


def test_load_schedule_rejects_overlapping_rows() -> None:
    repo = FakeRepository(
        holidays=[
            THANKSGIVING,
            HolidayPeriod(
                "Overlap", date(2026, 11, 27), date(2026, 11, 30), ScheduleType.BREAK, "x", None
            ),
        ]
    )
    assert run(load_schedule(date(2026, 11, 26), repo)).schedule_type == ScheduleType.BREAK
    with pytest.raises(ScheduleDataError):
        run(load_schedule(date(2026, 11, 27), repo))
