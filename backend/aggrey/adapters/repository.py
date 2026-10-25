"""The dining data repository interface.

Plain lookups only. Choosing which schedule or menu applies to a date is domain
logic (roadmap M4/M5) and does not belong here.
"""

from datetime import date
from typing import Protocol

from aggrey.domain.models import (
    HolidayPeriod,
    MealType,
    MenuItem,
    MenuScope,
    ScheduleType,
    ServiceHours,
)


class RepositoryError(Exception):
    """The dining data could not be read (connection, timeout, or query failure)."""


class DiningRepository(Protocol):
    async def find_overrides(self, day: date) -> list[HolidayPeriod]:
        """Holiday or break periods whose inclusive date range contains `day`."""
        ...

    async def get_hours(self, schedule: ScheduleType, meal: MealType) -> ServiceHours | None:
        """The serving window for one meal on one schedule type, if it exists."""
        ...

    async def get_menu(
        self,
        scope: MenuScope,
        weekday: int | None,
        meal: MealType,
        station: str | None = None,
    ) -> list[MenuItem]:
        """Menu rows ordered by station, then display order.

        `weekday` is the ISO weekday for the weekly scope and None for holiday_sample.
        `station` matches case-insensitively when given.
        """
        ...

    async def search_food(
        self,
        term: str,
        scope: MenuScope,
        weekday: int | None,
        meal: MealType | None = None,
    ) -> list[MenuItem]:
        """Menu rows whose food item contains `term`, case-insensitively."""
        ...

    async def get_metadata(self, key: str) -> str | None:
        """The metadata value for `key`, if present."""
        ...
