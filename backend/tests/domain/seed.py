"""The `mvp_v1_3` hours and holiday rows from db/seed.sql, for domain tests."""

from datetime import date, time

from aggrey.adapters.fake import FakeRepository
from aggrey.domain.models import HolidayPeriod, MealType, ScheduleType, ServiceHours

W, E, H, B = ScheduleType.WEEKDAY, ScheduleType.WEEKEND, ScheduleType.HOLIDAY, ScheduleType.BREAK

HOURS = [
    ServiceHours(W, MealType.BREAKFAST, time(7, 30), time(9, 30)),
    ServiceHours(W, MealType.LUNCH, time(11), time(14)),
    ServiceHours(W, MealType.LITE_LUNCH, time(14), time(15)),
    ServiceHours(W, MealType.DINNER, time(17), time(20)),
    ServiceHours(E, MealType.BRUNCH, time(10, 30), time(13, 30)),
    ServiceHours(E, MealType.DINNER, time(17), time(20)),
    ServiceHours(H, MealType.BRUNCH, time(10, 30), time(13, 30)),
    ServiceHours(H, MealType.DINNER, time(17), time(20)),
    ServiceHours(B, MealType.BRUNCH, time(10), time(11)),
    ServiceHours(B, MealType.DINNER, time(16), time(18)),
]


def _holiday(name: str, start: date, end: date, kind: ScheduleType, status: str) -> HolidayPeriod:
    return HolidayPeriod(name, start, end, kind, status, None)


HOLIDAYS = [
    _holiday("Labor Day", date(2026, 9, 7), date(2026, 9, 7), H, "calendar_date; mvp_hours"),
    _holiday(
        "Thanksgiving Holiday",
        date(2026, 11, 25),
        date(2026, 11, 27),
        B,
        "calendar_date; user_confirmed_hours",
    ),
    _holiday(
        "Virtual Classes, Reading Day & Exams",
        date(2026, 11, 30),
        date(2026, 12, 12),
        B,
        "pending_confirmation",
    ),
    _holiday(
        "Martin Luther King Jr. Holiday",
        date(2027, 1, 18),
        date(2027, 1, 18),
        H,
        "calendar_date; mvp_hours",
    ),
]


def windows(schedule: ScheduleType) -> list[ServiceHours]:
    return [h for h in HOURS if h.schedule_type == schedule]


def repository() -> FakeRepository:
    return FakeRepository(hours=HOURS, holidays=HOLIDAYS, metadata={"timezone": "America/New_York"})
