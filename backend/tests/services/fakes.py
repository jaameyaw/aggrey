"""Small menus and a recording fake for the service unit tests."""

from collections.abc import Iterable
from datetime import date

from aggrey.adapters.fake import FakeRepository
from aggrey.domain.models import MealType, MenuItem, MenuScope, ScheduleType, ServiceHours
from aggrey.domain.schedule import DaySchedule
from tests.domain.seed import HOLIDAYS, HOURS

MONDAY = DaySchedule(date(2026, 10, 26), ScheduleType.WEEKDAY)
SATURDAY = DaySchedule(date(2026, 10, 31), ScheduleType.WEEKEND)
THANKSGIVING = DaySchedule(date(2026, 11, 25), ScheduleType.BREAK, HOLIDAYS[1])


def weekly(day: int, meal: MealType, station: str, food: str, order: int) -> MenuItem:
    return MenuItem(MenuScope.WEEKLY, day, meal, station, food, order)


def sample(meal: MealType, station: str, food: str, order: int) -> MenuItem:
    return MenuItem(MenuScope.HOLIDAY_SAMPLE, None, meal, station, food, order)


L, BR, D = MealType.LUNCH, MealType.BRUNCH, MealType.DINNER

MENUS = [
    weekly(1, L, "Pizza", "Pepperoni Pizza", 2),
    weekly(1, L, "Pizza", "Cheese Pizza", 1),
    weekly(1, L, "Grill / sandwich", "Onion Rings", 6),
    weekly(1, L, "Grill / sandwich", "Beef Patty", 1),
    weekly(1, L, "Main hot-food", "BBQ Chicken", 1),
    weekly(1, D, "Dinner / turntable", "Fried Chicken", 1),
    weekly(1, MealType.BREAKFAST, "Breakfast", "Scrambled Eggs", 1),
    # Wednesday weekly rows must never answer for a holiday or break Wednesday.
    weekly(3, D, "Dinner / turntable", "Wednesday Meatloaf", 1),
    weekly(6, BR, "Grill / sandwich", "Saturday Waffle", 1),
    weekly(6, D, "Dinner / turntable", "Beef Stroganoff", 1),
    sample(BR, "Grill / sandwich", "Sample Waffle", 1),
    sample(D, "Dinner / turntable", "Beef Stroganoff", 1),
]


class RecordingRepository(FakeRepository):
    """Records every menu query so tests can check which rows were read."""

    def __init__(
        self, *, menus: Iterable[MenuItem] = MENUS, hours: Iterable[ServiceHours] = HOURS
    ) -> None:
        super().__init__(menus=menus, hours=hours)
        self.menu_calls: list[tuple[MenuScope, int | None, MealType]] = []

    async def get_menu(
        self,
        scope: MenuScope,
        weekday: int | None,
        meal: MealType,
        station: str | None = None,
    ) -> list[MenuItem]:
        self.menu_calls.append((scope, weekday, meal))
        return await super().get_menu(scope, weekday, meal, station)


def hours_without(meal: MealType, schedule: ScheduleType) -> list[ServiceHours]:
    return [h for h in HOURS if not (h.meal_type == meal and h.schedule_type == schedule)]
