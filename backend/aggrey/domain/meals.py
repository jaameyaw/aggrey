"""Meal validation and time-of-day rules (spec sections 6.3 and 6.4).

Serving windows come from the `hours` table; only which meals each schedule
serves is a fixed rule (schema doc section 9).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import time
from enum import StrEnum
from itertools import pairwise

from aggrey.domain.models import MealType, ScheduleType, ServiceHours
from aggrey.domain.schedule import ScheduleDataError

_WEEKDAY_MEALS = (MealType.BREAKFAST, MealType.LUNCH, MealType.LITE_LUNCH, MealType.DINNER)
_BRUNCH_MEALS = (MealType.BRUNCH, MealType.DINNER)

MEALS_BY_SCHEDULE: dict[ScheduleType, tuple[MealType, ...]] = {
    ScheduleType.WEEKDAY: _WEEKDAY_MEALS,
    ScheduleType.WEEKEND: _BRUNCH_MEALS,
    ScheduleType.HOLIDAY: _BRUNCH_MEALS,
    ScheduleType.BREAK: _BRUNCH_MEALS,
}


@dataclass(frozen=True, slots=True)
class MealCheck:
    meal: MealType
    served: bool
    meals_today: tuple[MealType, ...]
    # The meal whose menu answers instead, when one does: brunch for lunch on a
    # weekend, holiday, or break day. Breakfast and Lite Lunch get none.
    substitute: MealType | None = None


class MealState(StrEnum):
    NOT_STARTED = "not_started"
    SERVING = "serving"
    OVER = "over"


@dataclass(frozen=True, slots=True)
class DayStatus:
    current: ServiceHours | None
    # The meal being served now, otherwise the first one starting later today.
    next: ServiceHours | None


@dataclass(frozen=True, slots=True)
class FinishedMeal:
    meal: MealType
    # None when no more meals are served today.
    next: ServiceHours | None


def meals_served(schedule: ScheduleType) -> tuple[MealType, ...]:
    return MEALS_BY_SCHEDULE[schedule]


def check_meal(meal: MealType, schedule: ScheduleType) -> MealCheck:
    meals_today = meals_served(schedule)
    if meal in meals_today:
        return MealCheck(meal, True, meals_today)
    substitute = (
        MealType.BRUNCH if meal == MealType.LUNCH and MealType.BRUNCH in meals_today else None
    )
    return MealCheck(meal, False, meals_today, substitute)


def meal_state(window: ServiceHours, at: time) -> MealState:
    """Served from the start time up to, but not including, the end time."""
    if at < window.start_time:
        return MealState.NOT_STARTED
    if at < window.end_time:
        return MealState.SERVING
    return MealState.OVER


def day_status(windows: Sequence[ServiceHours], at: time) -> DayStatus:
    """Where `at` falls among one day's serving windows (all from one schedule)."""
    ordered = _ordered_windows(windows)
    for window in ordered:
        state = meal_state(window, at)
        if state is MealState.SERVING:
            return DayStatus(window, window)
        if state is MealState.NOT_STARTED:
            return DayStatus(None, window)
    return DayStatus(None, None)


def finished_meal(meal: MealType, windows: Sequence[ServiceHours], at: time) -> FinishedMeal | None:
    """The N-14 rule: None unless `meal` is over today, else what comes next today."""
    window = next((w for w in _ordered_windows(windows) if w.meal_type == meal), None)
    if window is None or meal_state(window, at) is not MealState.OVER:
        return None
    return FinishedMeal(meal, day_status(windows, at).next)


def _ordered_windows(windows: Sequence[ServiceHours]) -> list[ServiceHours]:
    ordered = sorted(windows, key=lambda w: (w.start_time, w.end_time))
    schedules = {w.schedule_type for w in ordered}
    if len(schedules) > 1:
        raise ScheduleDataError(f"serving windows mix schedules: {sorted(schedules)}")
    meals = [w.meal_type for w in ordered]
    if len(set(meals)) != len(meals):
        raise ScheduleDataError(f"a meal has more than one serving window: {meals}")
    for window in ordered:
        if window.start_time >= window.end_time:
            raise ScheduleDataError(f"{window.meal_type} window ends before it starts")
    for earlier, later in pairwise(ordered):
        if later.start_time < earlier.end_time:
            raise ScheduleDataError(
                f"{earlier.meal_type} and {later.meal_type} serving windows overlap"
            )
    return ordered
