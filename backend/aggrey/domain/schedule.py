"""Schedule resolution (spec section 6.2, schema doc section 8)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from aggrey.domain.models import HolidayPeriod, ScheduleType

_OVERRIDE_TYPES = frozenset({ScheduleType.HOLIDAY, ScheduleType.BREAK})


class ScheduleDataError(Exception):
    """The stored dining data is inconsistent, so no answer can be chosen safely."""


class OverrideSource(Protocol):
    async def find_overrides(self, day: date) -> list[HolidayPeriod]: ...


@dataclass(frozen=True, slots=True)
class DaySchedule:
    day: date
    schedule_type: ScheduleType
    # The holiday or break row, kept so replies can name it and disclose its
    # verification status. Which statuses count as provisional is open (N-43).
    override: HolidayPeriod | None = None


def resolve_schedule(day: date, overrides: Sequence[HolidayPeriod]) -> DaySchedule:
    """Holiday or break override first, then weekend, then weekday."""
    if len(overrides) > 1:
        names = ", ".join(sorted(o.name for o in overrides))
        raise ScheduleDataError(f"{day} matches more than one holiday or break: {names}")
    if overrides:
        override = overrides[0]
        if override.schedule_type not in _OVERRIDE_TYPES:
            raise ScheduleDataError(
                f"holiday {override.name!r} has schedule type {override.schedule_type}"
            )
        if not override.start_date <= day <= override.end_date:
            raise ScheduleDataError(f"holiday {override.name!r} does not cover {day}")
        return DaySchedule(day, override.schedule_type, override)
    if day.isoweekday() >= 6:
        return DaySchedule(day, ScheduleType.WEEKEND)
    return DaySchedule(day, ScheduleType.WEEKDAY)


async def load_schedule(day: date, source: OverrideSource) -> DaySchedule:
    return resolve_schedule(day, await source.find_overrides(day))
