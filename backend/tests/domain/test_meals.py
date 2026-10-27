from datetime import time

import pytest

from aggrey.domain.meals import (
    DayStatus,
    FinishedMeal,
    MealCheck,
    MealState,
    check_meal,
    day_status,
    finished_meal,
    meal_state,
    meals_served,
)
from aggrey.domain.models import MealType, ScheduleType, ServiceHours
from aggrey.domain.schedule import ScheduleDataError
from tests.domain.seed import windows

WEEKDAY = windows(ScheduleType.WEEKDAY)
BREAKFAST, LUNCH, LITE_LUNCH, DINNER = WEEKDAY
BRUNCH_MEALS = (MealType.BRUNCH, MealType.DINNER)


def test_meals_served() -> None:
    assert meals_served(ScheduleType.WEEKDAY) == (
        MealType.BREAKFAST,
        MealType.LUNCH,
        MealType.LITE_LUNCH,
        MealType.DINNER,
    )
    for schedule in (ScheduleType.WEEKEND, ScheduleType.HOLIDAY, ScheduleType.BREAK):
        assert meals_served(schedule) == BRUNCH_MEALS


def test_served_meal() -> None:
    check = check_meal(MealType.LUNCH, ScheduleType.WEEKDAY)
    assert check.served
    assert check.substitute is None


@pytest.mark.parametrize(
    "schedule", [ScheduleType.WEEKEND, ScheduleType.HOLIDAY, ScheduleType.BREAK]
)
def test_lunch_on_a_brunch_day_is_answered_with_brunch(schedule: ScheduleType) -> None:
    assert check_meal(MealType.LUNCH, schedule) == MealCheck(
        MealType.LUNCH, False, BRUNCH_MEALS, MealType.BRUNCH
    )


@pytest.mark.parametrize("meal", [MealType.BREAKFAST, MealType.LITE_LUNCH])
@pytest.mark.parametrize(
    "schedule", [ScheduleType.WEEKEND, ScheduleType.HOLIDAY, ScheduleType.BREAK]
)
def test_breakfast_and_lite_lunch_on_a_brunch_day_get_no_menu(
    meal: MealType, schedule: ScheduleType
) -> None:
    assert check_meal(meal, schedule) == MealCheck(meal, False, BRUNCH_MEALS)


def test_brunch_on_a_weekday_is_not_served() -> None:
    check = check_meal(MealType.BRUNCH, ScheduleType.WEEKDAY)
    assert not check.served
    assert check.substitute is None
    assert check.meals_today == meals_served(ScheduleType.WEEKDAY)


@pytest.mark.parametrize(
    ("at", "state"),
    [
        (time(10, 59, 59), MealState.NOT_STARTED),
        (time(11), MealState.SERVING),
        (time(13, 59, 59), MealState.SERVING),
        (time(14), MealState.OVER),
    ],
)
def test_lunch_window_edges(at: time, state: MealState) -> None:
    assert meal_state(LUNCH, at) == state


def test_two_pm_is_lite_lunch_not_lunch() -> None:
    assert day_status(WEEKDAY, time(14)) == DayStatus(LITE_LUNCH, LITE_LUNCH)


@pytest.mark.parametrize(
    ("at", "current", "next_meal"),
    [
        (time(0), None, BREAKFAST),
        (time(7, 30), BREAKFAST, BREAKFAST),
        (time(10), None, LUNCH),
        (time(12), LUNCH, LUNCH),
        (time(15, 30), None, DINNER),
        (time(19, 59), DINNER, DINNER),
        (time(20), None, None),
        (time(23, 59), None, None),
    ],
)
def test_day_status(at: time, current: ServiceHours | None, next_meal: ServiceHours | None) -> None:
    assert day_status(WEEKDAY, at) == DayStatus(current, next_meal)


def test_day_status_ignores_input_order() -> None:
    assert day_status(list(reversed(WEEKDAY)), time(10)) == DayStatus(None, LUNCH)


def test_meal_not_over_is_not_finished() -> None:
    assert finished_meal(MealType.LUNCH, WEEKDAY, time(12)) is None
    assert finished_meal(MealType.DINNER, WEEKDAY, time(8)) is None


def test_meal_without_a_window_is_not_finished() -> None:
    assert finished_meal(MealType.BRUNCH, WEEKDAY, time(23)) is None


def test_finished_lunch_points_to_lite_lunch() -> None:
    assert finished_meal(MealType.LUNCH, WEEKDAY, time(14, 30)) == FinishedMeal(
        MealType.LUNCH, LITE_LUNCH
    )


def test_finished_lunch_points_to_dinner() -> None:
    assert finished_meal(MealType.LUNCH, WEEKDAY, time(15, 30)) == FinishedMeal(
        MealType.LUNCH, DINNER
    )


def test_finished_dinner_has_nothing_next() -> None:
    assert finished_meal(MealType.DINNER, WEEKDAY, time(20, 30)) == FinishedMeal(
        MealType.DINNER, None
    )


def test_overlapping_windows_are_a_data_error() -> None:
    overlap = ServiceHours(ScheduleType.WEEKDAY, MealType.LITE_LUNCH, time(13, 30), time(15))
    with pytest.raises(ScheduleDataError, match="overlap"):
        day_status([LUNCH, overlap], time(12))


def test_mixed_schedules_are_a_data_error() -> None:
    brunch = windows(ScheduleType.WEEKEND)[0]
    with pytest.raises(ScheduleDataError, match="mix schedules"):
        day_status([LUNCH, brunch], time(12))


def test_duplicate_meal_window_is_a_data_error() -> None:
    late = ServiceHours(ScheduleType.WEEKDAY, MealType.LUNCH, time(15), time(16))
    with pytest.raises(ScheduleDataError, match="more than one"):
        day_status([LUNCH, late], time(12))


def test_backwards_window_is_a_data_error() -> None:
    bad = ServiceHours(ScheduleType.WEEKDAY, MealType.LUNCH, time(14), time(11))
    with pytest.raises(ScheduleDataError, match="ends before"):
        day_status([bad], time(12))
