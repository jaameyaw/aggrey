"""In-memory dining repository for unit tests. Mirrors PostgresRepository behaviour."""

from collections.abc import Iterable, Mapping
from datetime import date

from aggrey.domain.models import (
    HolidayPeriod,
    MealType,
    MenuItem,
    MenuScope,
    ScheduleType,
    ServiceHours,
)


class FakeRepository:
    def __init__(
        self,
        *,
        menus: Iterable[MenuItem] = (),
        hours: Iterable[ServiceHours] = (),
        holidays: Iterable[HolidayPeriod] = (),
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        self.menus = list(menus)
        self.hours = list(hours)
        self.holidays = list(holidays)
        self.metadata = dict(metadata or {})

    async def find_overrides(self, day: date) -> list[HolidayPeriod]:
        matches = [h for h in self.holidays if h.start_date <= day <= h.end_date]
        return sorted(matches, key=lambda h: (h.start_date, h.name))

    async def get_hours(self, schedule: ScheduleType, meal: MealType) -> ServiceHours | None:
        for window in self.hours:
            if window.schedule_type == schedule and window.meal_type == meal:
                return window
        return None

    async def get_menu(
        self,
        scope: MenuScope,
        weekday: int | None,
        meal: MealType,
        station: str | None = None,
    ) -> list[MenuItem]:
        wanted_station = station.strip().lower() if station is not None else None
        matches = [
            item
            for item in self.menus
            if item.menu_scope == scope
            and item.day_of_week == weekday
            and item.meal_type == meal
            and (wanted_station is None or item.station.strip().lower() == wanted_station)
        ]
        return sorted(matches, key=lambda item: (item.station, item.display_order))

    async def search_food(
        self,
        term: str,
        scope: MenuScope,
        weekday: int | None,
        meal: MealType | None = None,
    ) -> list[MenuItem]:
        needle = term.strip().lower()
        meal_order = list(MealType)
        matches = [
            item
            for item in self.menus
            if item.menu_scope == scope
            and item.day_of_week == weekday
            and (meal is None or item.meal_type == meal)
            and needle in item.food_item.lower()
        ]
        return sorted(
            matches,
            key=lambda item: (meal_order.index(item.meal_type), item.station, item.display_order),
        )

    async def get_metadata(self, key: str) -> str | None:
        return self.metadata.get(key)
