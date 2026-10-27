"""Roadmap Section 6 rows that depend on dates and schedules, with a fixed clock.

Menu contents and reply wording belong to M5 and M6; these tests check the
date, schedule, meal, and time-of-day facts those replies are built from.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from aggrey.domain.dates import ResolvedDate, UnrecognizedDate, resolve_date, to_local
from aggrey.domain.meals import DayStatus, FinishedMeal, MealCheck, check_meal, day_status
from aggrey.domain.meals import finished_meal as find_finished_meal
from aggrey.domain.models import MealType, ScheduleType, ServiceHours
from aggrey.domain.schedule import DaySchedule, load_schedule
from tests.conftest import run
from tests.domain.seed import repository, windows

NY = ZoneInfo("America/New_York")
B, L, LL, D, BR = (
    MealType.BREAKFAST,
    MealType.LUNCH,
    MealType.LITE_LUNCH,
    MealType.DINNER,
    MealType.BRUNCH,
)


@dataclass(frozen=True)
class Facts:
    day: date
    schedule: DaySchedule
    windows: list[ServiceHours]
    meal: MealCheck | None
    # Only for questions about today (spec 6.4).
    status: DayStatus | None
    finished: FinishedMeal | None


def ask(words: str, now: datetime, meal: MealType | None = None) -> Facts:
    resolved = resolve_date(words.split(), now, NY)
    assert isinstance(resolved, ResolvedDate)
    schedule = run(load_schedule(resolved.day, repository()))
    day_windows = windows(schedule.schedule_type)
    is_today = resolved.day == to_local(now, NY).date()
    at = to_local(now, NY).time()
    check = check_meal(meal, schedule.schedule_type) if meal else None
    finished = None
    if is_today and check is not None:
        asked = check.meal if check.served else check.substitute
        finished = find_finished_meal(asked, day_windows, at) if asked else None
    return Facts(
        resolved.day,
        schedule,
        day_windows,
        check,
        day_status(day_windows, at) if is_today else None,
        finished,
    )


def at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=NY)


def window(facts: Facts, meal: MealType) -> tuple[time, time]:
    match = next(w for w in facts.windows if w.meal_type == meal)
    return match.start_time, match.end_time


MON = date(2026, 10, 26)


def test_row_7_saturday_lunch_is_answered_with_brunch() -> None:
    facts = ask("whats for lunch", at(date(2026, 10, 31), 9), L)
    assert facts.schedule.schedule_type == ScheduleType.WEEKEND
    assert facts.meal == MealCheck(L, False, (BR, D), BR)
    assert facts.finished is None


def test_row_8_saturday_breakfast_is_not_served() -> None:
    facts = ask("whats for breakfast", at(date(2026, 10, 31), 9), B)
    assert facts.meal == MealCheck(B, False, (BR, D))


def test_row_9_sunday_brunch_hours() -> None:
    facts = ask("what time is brunch", at(date(2026, 11, 1), 9), BR)
    assert facts.schedule.schedule_type == ScheduleType.WEEKEND
    assert window(facts, BR) == (time(10, 30), time(13, 30))


def test_row_10_thanksgiving_lunch() -> None:
    facts = ask("whats for lunch", at(date(2026, 11, 25), 9), L)
    assert facts.schedule.schedule_type == ScheduleType.BREAK
    assert facts.schedule.override is not None
    assert facts.schedule.override.name == "Thanksgiving Holiday"
    assert facts.meal == MealCheck(L, False, (BR, D), BR)
    assert window(facts, BR) == (time(10), time(11))
    assert window(facts, D) == (time(16), time(18))


def test_row_11_thanksgiving_dinner_is_a_break_day_meal() -> None:
    facts = ask("whats for dinner", at(date(2026, 11, 25), 9), D)
    assert facts.schedule.schedule_type == ScheduleType.BREAK
    assert facts.meal is not None
    assert facts.meal.served
    assert window(facts, D) == (time(16), time(18))


def test_row_12_virtual_classes_dinner_carries_pending_status() -> None:
    facts = ask("what time is dinner", at(date(2026, 12, 1), 9), D)
    assert facts.schedule.schedule_type == ScheduleType.BREAK
    assert facts.schedule.override is not None
    assert facts.schedule.override.verification_status == "pending_confirmation"
    assert window(facts, D) == (time(16), time(18))


def test_row_13_mlk_day_brunch_hours() -> None:
    facts = ask("what time is brunch", at(date(2027, 1, 18), 9), BR)
    assert facts.schedule.schedule_type == ScheduleType.HOLIDAY
    assert window(facts, BR) == (time(10, 30), time(13, 30))


def test_row_14_labor_day_breakfast_is_not_served() -> None:
    facts = ask("whats for breakfast", at(date(2026, 9, 7), 8), B)
    assert facts.schedule.schedule_type == ScheduleType.HOLIDAY
    assert facts.meal == MealCheck(B, False, (BR, D))


def test_row_15_lite_lunch_hours() -> None:
    facts = ask("what time is lite lunch", at(MON, 9), LL)
    assert window(facts, LL) == (time(14), time(15))


def test_row_20_closed_between_meals() -> None:
    facts = ask("is the caf open", at(MON, 15, 30))
    assert facts.status is not None
    assert facts.status.current is None
    assert facts.status.next is not None
    assert facts.status.next.meal_type == D
    assert facts.status.next.start_time == time(17)


def test_row_21_lunch_being_served() -> None:
    facts = ask("is the caf still open", at(MON, 12))
    assert facts.status is not None
    assert facts.status.current is not None
    assert facts.status.current.meal_type == L
    assert facts.status.current.end_time == time(14)


def test_row_22_sunday_asking_for_tomorrow_gets_a_weekday() -> None:
    facts = ask("whats for lunch tomorrow", at(date(2026, 10, 25), 12), L)
    assert facts.day == MON
    assert facts.schedule.schedule_type == ScheduleType.WEEKDAY
    assert facts.meal is not None
    assert facts.meal.served


def test_row_23_tomorrow_is_thanksgiving_break() -> None:
    facts = ask("whats for lunch tomorrow", at(date(2026, 11, 24), 12), L)
    assert facts.day == date(2026, 11, 25)
    assert facts.schedule.schedule_type == ScheduleType.BREAK
    assert facts.meal == MealCheck(L, False, (BR, D), BR)


@pytest.mark.parametrize("words", ["lunch on 11/25", "lunch yesterday", "lunch nov 25"])
def test_row_25_unsupported_date_is_not_guessed(words: str) -> None:
    assert isinstance(resolve_date(words.split(), at(MON, 12), NY), UnrecognizedDate)


def test_row_30_lunch_over_points_to_dinner() -> None:
    facts = ask("whats for lunch", at(MON, 15, 30), L)
    assert facts.finished is not None
    assert facts.finished.next is not None
    assert facts.finished.next.meal_type == D
    assert (facts.finished.next.start_time, facts.finished.next.end_time) == (time(17), time(20))


def test_row_31_lunch_over_points_to_lite_lunch() -> None:
    facts = ask("whats for lunch", at(MON, 14, 30), L)
    assert facts.finished is not None
    assert facts.finished.next is not None
    assert facts.finished.next.meal_type == LL
    assert facts.finished.next.end_time == time(15)


def test_row_35_dinner_over_for_today() -> None:
    facts = ask("whats for dinner", at(MON, 20, 30), D)
    assert facts.finished == FinishedMeal(D, None)


def test_row_32_tomorrow_uses_new_york_not_utc() -> None:
    facts = ask("whats for lunch tomorrow", datetime(2026, 10, 27, 2, tzinfo=UTC), L)
    assert facts.day == date(2026, 10, 27)
    assert facts.schedule.schedule_type == ScheduleType.WEEKDAY
    assert facts.finished is None  # finished-meal rule only applies to today


def test_row_33_no_date_means_today() -> None:
    facts = ask("whats for dinner", at(MON, 8), D)
    assert facts.day == MON
    assert facts.meal is not None
    assert facts.meal.served
    assert facts.finished is None


def test_row_34_thanksgiving_brunch_is_served() -> None:
    facts = ask("whats for brunch", at(date(2026, 11, 25), 9), BR)
    assert facts.schedule.schedule_type == ScheduleType.BREAK
    assert facts.meal is not None
    assert facts.meal.served


def test_weekend_lunch_after_brunch_applies_the_finished_rule_to_brunch() -> None:
    # Spec 6.3: Saturday 3:00 PM, lunch is not served and brunch is over; dinner is next.
    facts = ask("whats for lunch", at(date(2026, 10, 31), 15), L)
    assert facts.finished is not None
    assert facts.finished.meal == BR
    assert facts.finished.next is not None
    assert facts.finished.next.meal_type == D
