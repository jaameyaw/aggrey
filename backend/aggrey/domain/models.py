"""Dining data types shared by the domain rules and the repository.

The enums mirror the database enums in `db/schema.sql` exactly.
"""

from dataclasses import dataclass
from datetime import date, time
from enum import StrEnum


class MealType(StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    LITE_LUNCH = "lite_lunch"
    DINNER = "dinner"
    BRUNCH = "brunch"


class ScheduleType(StrEnum):
    WEEKDAY = "weekday"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"
    BREAK = "break"


class MenuScope(StrEnum):
    WEEKLY = "weekly"
    HOLIDAY_SAMPLE = "holiday_sample"


@dataclass(frozen=True, slots=True)
class MenuItem:
    menu_scope: MenuScope
    # ISO weekday (1 = Monday ... 7 = Sunday); None for the holiday_sample scope.
    day_of_week: int | None
    meal_type: MealType
    station: str
    food_item: str
    display_order: int


@dataclass(frozen=True, slots=True)
class ServiceHours:
    """A meal serving window. Not building hours (schema doc section 20)."""

    schedule_type: ScheduleType
    meal_type: MealType
    start_time: time
    end_time: time


@dataclass(frozen=True, slots=True)
class HolidayPeriod:
    name: str
    start_date: date
    end_date: date
    schedule_type: ScheduleType
    verification_status: str
    notes: str | None
