"""Serving hours lookup (spec 7.2; schema doc section 11).

These are meal serving windows, not building hours (schema doc section 20). Whether
an override's hours are provisional is open (N-43); `schedule.override` carries
its verification status for M6.
"""

from dataclasses import dataclass

from aggrey.adapters.repository import DiningRepository
from aggrey.domain.meals import meals_served
from aggrey.domain.models import MealType, ServiceHours
from aggrey.domain.schedule import DaySchedule
from aggrey.services.menu import require_served


@dataclass(frozen=True, slots=True)
class MealHours:
    schedule: DaySchedule
    window: ServiceHours


@dataclass(frozen=True, slots=True)
class HoursUnavailable:
    """A served meal with no hours row (6.7)."""

    schedule: DaySchedule
    meal: MealType


@dataclass(frozen=True, slots=True)
class DayHours:
    schedule: DaySchedule
    # Every served meal that has hours, in start-time order.
    windows: tuple[ServiceHours, ...]
    # Served meals with no hours row.
    missing: tuple[MealType, ...]


async def get_meal_hours(
    repository: DiningRepository, schedule: DaySchedule, meal: MealType
) -> MealHours | HoursUnavailable:
    require_served(schedule, meal)
    window = await repository.get_hours(schedule.schedule_type, meal)
    if window is None:
        return HoursUnavailable(schedule, meal)
    return MealHours(schedule, window)


async def get_day_hours(repository: DiningRepository, schedule: DaySchedule) -> DayHours:
    windows: list[ServiceHours] = []
    missing: list[MealType] = []
    for meal in meals_served(schedule.schedule_type):
        window = await repository.get_hours(schedule.schedule_type, meal)
        if window is None:
            missing.append(meal)
        else:
            windows.append(window)
    windows.sort(key=lambda w: (w.start_time, w.end_time))
    return DayHours(schedule, tuple(windows), tuple(missing))
