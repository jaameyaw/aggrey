"""Menu lookup (spec 6.6, 6.7, 7.1; schema doc section 10).

Results are facts, not reply text; M6 formats them.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from aggrey.adapters.repository import DiningRepository
from aggrey.domain.meals import meals_served
from aggrey.domain.models import MealType, MenuItem, MenuScope, ScheduleType
from aggrey.domain.schedule import DaySchedule
from aggrey.domain.text import normalize

_SAMPLE_SCHEDULES = frozenset({ScheduleType.HOLIDAY, ScheduleType.BREAK})


@dataclass(frozen=True, slots=True)
class StationMenu:
    name: str
    items: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MealMenu:
    schedule: DaySchedule
    meal: MealType
    # Stations in alphabetical order (spec 10), items in display order.
    stations: tuple[StationMenu, ...]
    # True for the holiday and break sample menus, which replies must label (6.5).
    sample: bool


class UnavailableReason(StrEnum):
    # Lite Lunch has hours but no food menu (6.7).
    LITE_LUNCH = "lite_lunch"
    # A valid meal with zero menu rows. Never fall back to another day (6.7).
    NO_ROWS = "no_rows"


@dataclass(frozen=True, slots=True)
class MenuUnavailable:
    schedule: DaySchedule
    meal: MealType
    reason: UnavailableReason


@dataclass(frozen=True, slots=True)
class StationNotFound:
    """The named station is not on this meal's menu that day (6.7)."""

    schedule: DaySchedule
    meal: MealType
    station: str
    available: tuple[str, ...]


def menu_source(schedule: DaySchedule) -> tuple[MenuScope, int | None]:
    """Which menu rows serve a day. Holidays and breaks never read `weekly` rows (6.6)."""
    if schedule.schedule_type in _SAMPLE_SCHEDULES:
        return MenuScope.HOLIDAY_SAMPLE, None
    return MenuScope.WEEKLY, schedule.day.isoweekday()


def require_served(schedule: DaySchedule, meal: MealType) -> None:
    """Callers check the meal with `check_meal` first (spec 6.3); this guards that."""
    if meal not in meals_served(schedule.schedule_type):
        raise ValueError(f"{meal} is not served on a {schedule.schedule_type} day")


def group_by_station(items: Sequence[MenuItem]) -> tuple[StationMenu, ...]:
    """Keeps the repository order: station, then display order."""
    stations: dict[str, list[str]] = {}
    for item in items:
        stations.setdefault(item.station, []).append(item.food_item)
    return tuple(StationMenu(name, tuple(foods)) for name, foods in stations.items())


async def get_meal_menu(
    repository: DiningRepository,
    schedule: DaySchedule,
    meal: MealType,
    station: str | None = None,
) -> MealMenu | MenuUnavailable | StationNotFound:
    """The menu for one served meal, optionally one station of it.

    `station` is a station name from the data (M6 maps aliases to names, spec 3.3).
    """
    require_served(schedule, meal)
    if meal == MealType.LITE_LUNCH:
        return MenuUnavailable(schedule, meal, UnavailableReason.LITE_LUNCH)
    scope, weekday = menu_source(schedule)
    stations = group_by_station(await repository.get_menu(scope, weekday, meal))
    if not stations:
        return MenuUnavailable(schedule, meal, UnavailableReason.NO_ROWS)
    if station is not None:
        wanted = normalize(station)
        chosen = tuple(s for s in stations if normalize(s.name) == wanted)
        if not chosen:
            return StationNotFound(schedule, meal, station, tuple(s.name for s in stations))
        stations = chosen
    return MealMenu(schedule, meal, stations, sample=scope == MenuScope.HOLIDAY_SAMPLE)
