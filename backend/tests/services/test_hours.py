from datetime import time

import pytest

from aggrey.domain.models import MealType, ScheduleType
from aggrey.services.hours import DayHours, HoursUnavailable, get_day_hours, get_meal_hours
from tests.conftest import run
from tests.services.fakes import MONDAY, SATURDAY, THANKSGIVING, RecordingRepository, hours_without


def test_meal_hours() -> None:
    result = run(get_meal_hours(RecordingRepository(), MONDAY, MealType.LITE_LUNCH))
    assert not isinstance(result, HoursUnavailable)
    assert (result.window.start_time, result.window.end_time) == (time(14), time(15))
    assert result.schedule == MONDAY


def test_break_hours_and_override_are_carried() -> None:
    result = run(get_meal_hours(RecordingRepository(), THANKSGIVING, MealType.DINNER))
    assert not isinstance(result, HoursUnavailable)
    assert (result.window.start_time, result.window.end_time) == (time(16), time(18))
    assert result.schedule.override is not None
    assert result.schedule.override.name == "Thanksgiving Holiday"


def test_missing_hours_row() -> None:
    repository = RecordingRepository(hours=hours_without(MealType.DINNER, ScheduleType.WEEKDAY))
    assert run(get_meal_hours(repository, MONDAY, MealType.DINNER)) == HoursUnavailable(
        MONDAY, MealType.DINNER
    )


def test_meal_not_served_is_a_caller_error() -> None:
    with pytest.raises(ValueError, match="not served"):
        run(get_meal_hours(RecordingRepository(), SATURDAY, MealType.LUNCH))


def test_day_hours_in_start_time_order() -> None:
    result = run(get_day_hours(RecordingRepository(), MONDAY))
    assert [w.meal_type for w in result.windows] == [
        MealType.BREAKFAST,
        MealType.LUNCH,
        MealType.LITE_LUNCH,
        MealType.DINNER,
    ]
    assert result.missing == ()


def test_day_hours_reports_missing_meals() -> None:
    repository = RecordingRepository(hours=hours_without(MealType.BRUNCH, ScheduleType.WEEKEND))
    result = run(get_day_hours(repository, SATURDAY))
    assert result == DayHours(
        SATURDAY,
        tuple(w for w in repository.hours if w.schedule_type == ScheduleType.WEEKEND),
        (MealType.BRUNCH,),
    )
