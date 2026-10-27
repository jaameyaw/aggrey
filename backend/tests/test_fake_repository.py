from datetime import date, time

from aggrey.adapters.fake import FakeRepository
from aggrey.domain.models import (
    HolidayPeriod,
    MealType,
    MenuItem,
    MenuScope,
    ScheduleType,
    ServiceHours,
)
from tests.conftest import run


def _item(
    food: str,
    *,
    station: str = "Grill",
    order: int = 1,
    meal: MealType = MealType.LUNCH,
    weekday: int | None = 1,
    scope: MenuScope = MenuScope.WEEKLY,
) -> MenuItem:
    return MenuItem(scope, weekday, meal, station, food, order)


REPOSITORY = FakeRepository(
    menus=[
        _item("Fries", order=2),
        _item("Wings", order=1),
        _item("Caesar Salad", station="Deli"),
        _item("Wings", weekday=2),
        _item("Chicken Wings", meal=MealType.DINNER),
        _item("Pancakes", meal=MealType.BRUNCH, weekday=None, scope=MenuScope.HOLIDAY_SAMPLE),
    ],
    hours=[ServiceHours(ScheduleType.WEEKDAY, MealType.LUNCH, time(11), time(14))],
    holidays=[
        HolidayPeriod(
            "Thanksgiving Holiday",
            date(2026, 11, 25),
            date(2026, 11, 27),
            ScheduleType.BREAK,
            "calendar_date",
            None,
        )
    ],
    metadata={"timezone": "America/New_York"},
)


def test_menu_is_filtered_and_ordered_by_station_then_display_order() -> None:
    items = run(REPOSITORY.get_menu(MenuScope.WEEKLY, 1, MealType.LUNCH))

    assert [i.food_item for i in items] == ["Caesar Salad", "Wings", "Fries"]


def test_menu_station_matches_case_insensitively() -> None:
    items = run(REPOSITORY.get_menu(MenuScope.WEEKLY, 1, MealType.LUNCH, station=" grill "))

    assert [i.food_item for i in items] == ["Wings", "Fries"]


def test_holiday_sample_menu_uses_no_weekday() -> None:
    items = run(REPOSITORY.get_menu(MenuScope.HOLIDAY_SAMPLE, None, MealType.BRUNCH))

    assert [i.food_item for i in items] == ["Pancakes"]


def test_hours_lookup() -> None:
    window = run(REPOSITORY.get_hours(ScheduleType.WEEKDAY, MealType.LUNCH))

    assert window is not None
    assert (window.start_time, window.end_time) == (time(11), time(14))
    assert run(REPOSITORY.get_hours(ScheduleType.WEEKEND, MealType.BRUNCH)) is None


def test_overrides_include_both_range_ends() -> None:
    assert run(REPOSITORY.find_overrides(date(2026, 11, 24))) == []
    assert len(run(REPOSITORY.find_overrides(date(2026, 11, 25)))) == 1
    assert len(run(REPOSITORY.find_overrides(date(2026, 11, 27)))) == 1


def test_metadata_lookup() -> None:
    assert run(REPOSITORY.get_metadata("timezone")) == "America/New_York"
    assert run(REPOSITORY.get_metadata("missing")) is None
