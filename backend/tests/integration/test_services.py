"""M5 services against the seeded `mvp_v1_3` database (roadmap Section 6 data rows)."""

from collections.abc import Awaitable, Callable
from datetime import date, time

import pytest

from aggrey.adapters.postgres import PostgresRepository
from aggrey.domain.food_match import compile_query
from aggrey.domain.models import MealType, MenuScope, ScheduleType
from aggrey.domain.schedule import DaySchedule, load_schedule
from aggrey.services.food_search import FoodMatch, FoodSearch, search_food
from aggrey.services.hours import HoursUnavailable, MealHours, get_meal_hours
from aggrey.services.menu import (
    MealMenu,
    MenuUnavailable,
    StationMenu,
    UnavailableReason,
    get_meal_menu,
)
from tests.integration.conftest import requires_database, with_repository

pytestmark = requires_database

B, L, LL, D, BR = (
    MealType.BREAKFAST,
    MealType.LUNCH,
    MealType.LITE_LUNCH,
    MealType.DINNER,
    MealType.BRUNCH,
)
MON, TUE, FRI = date(2026, 10, 26), date(2026, 10, 27), date(2026, 10, 30)
SAT, SUN = date(2026, 10, 31), date(2026, 11, 1)
THANKSGIVING, VIRTUAL_CLASSES = date(2026, 11, 25), date(2026, 12, 1)
LABOR_DAY, MLK_DAY = date(2026, 9, 7), date(2027, 1, 18)


def on[T](
    dsn: str, day: date, action: Callable[[PostgresRepository, DaySchedule], Awaitable[T]]
) -> T:
    async def go(repository: PostgresRepository) -> T:
        return await action(repository, await load_schedule(day, repository))

    return with_repository(dsn, go)


def menu(dsn: str, day: date, meal: MealType, station: str | None = None) -> object:
    return on(dsn, day, lambda r, s: get_meal_menu(r, s, meal, station))


def meal_menu(dsn: str, day: date, meal: MealType, station: str | None = None) -> MealMenu:
    result = menu(dsn, day, meal, station)
    assert isinstance(result, MealMenu)
    return result


def hours(dsn: str, day: date, meal: MealType) -> tuple[time, time]:
    result = on(dsn, day, lambda r, s: get_meal_hours(r, s, meal))
    assert isinstance(result, MealHours)
    return result.window.start_time, result.window.end_time


def food(dsn: str, day: date, keyword: str, meal: MealType | None = None) -> FoodSearch:
    return on(dsn, day, lambda r, s: search_food(r, s, keyword, meal))


def test_row_1_monday_breakfast(readonly_dsn: str) -> None:
    result = meal_menu(readonly_dsn, MON, B)
    assert [s.name for s in result.stations] == ["Breakfast"]
    items = result.stations[0].items
    assert len(items) == 9
    assert (items[0], items[-1]) == ("Scrambled Eggs", "Classic Oatmeal")


def test_row_2_and_4_monday_lunch_has_five_stations_alphabetically(readonly_dsn: str) -> None:
    result = meal_menu(readonly_dsn, MON, L)
    assert [s.name for s in result.stations] == [
        "Grill / sandwich",
        "Main hot-food",
        "Pasta",
        "Pizza",
        "Special",
    ]
    assert all(s.items for s in result.stations)


def test_row_3_monday_pizza_station(readonly_dsn: str) -> None:
    assert meal_menu(readonly_dsn, MON, L, "pizza").stations == (
        StationMenu(
            "Pizza",
            ("Cheese Pizza", "Pepperoni Pizza", "Roasted Vegetable Pizza", "Margherita Pizza"),
        ),
    )


def test_row_6_tuesday_special(readonly_dsn: str) -> None:
    assert meal_menu(readonly_dsn, TUE, L, "Special").stations == (
        StationMenu("Special", ("Taco Bar",)),
    )


def test_row_7_saturday_brunch_is_the_weekly_menu(readonly_dsn: str) -> None:
    result = meal_menu(readonly_dsn, SAT, BR)
    assert not result.sample
    assert [s.name for s in result.stations] == [
        "Breakfast",
        "Grill / sandwich",
        "Main hot-food",
        "Pizza",
    ]
    assert sum(len(s.items) for s in result.stations) == 22


@pytest.mark.parametrize(
    ("day", "meal", "window"),
    [
        (SUN, BR, (time(10, 30), time(13, 30))),  # row 9
        (MLK_DAY, BR, (time(10, 30), time(13, 30))),  # row 13
        (MON, LL, (time(14), time(15))),  # row 15
        (THANKSGIVING, BR, (time(10), time(11))),  # row 10
        (THANKSGIVING, D, (time(16), time(18))),  # rows 10, 11
        (MON, D, (time(17), time(20))),  # rows 20, 30
    ],
)
def test_rows_9_10_13_15_hours(
    readonly_dsn: str, day: date, meal: MealType, window: tuple[time, time]
) -> None:
    assert hours(readonly_dsn, day, meal) == window


def test_row_10_and_34_thanksgiving_brunch_is_the_labeled_sample(readonly_dsn: str) -> None:
    result = meal_menu(readonly_dsn, THANKSGIVING, BR)
    assert result.schedule.schedule_type == ScheduleType.BREAK
    assert result.sample
    items = [item for s in result.stations for item in s.items]
    assert "Blueberry Pancakes" in items
    assert len(items) == 22


def test_row_11_thanksgiving_dinner_is_the_sample_not_wednesday(readonly_dsn: str) -> None:
    result = meal_menu(readonly_dsn, THANKSGIVING, D)
    assert result.sample
    assert result.stations == (
        StationMenu(
            "Dinner / turntable",
            ("Beef Stroganoff", "Butter Egg Noodle", "Steamed Broccoli", "Oregano Roasted Carrots"),
        ),
    )


def test_row_12_virtual_classes_dinner_carries_pending_status(readonly_dsn: str) -> None:
    result = on(readonly_dsn, VIRTUAL_CLASSES, lambda r, s: get_meal_hours(r, s, D))
    assert isinstance(result, MealHours)
    assert (result.window.start_time, result.window.end_time) == (time(16), time(18))
    assert result.schedule.override is not None
    assert result.schedule.override.verification_status == "pending_confirmation"


def test_row_14_labor_day_brunch_is_the_sample(readonly_dsn: str) -> None:
    result = meal_menu(readonly_dsn, LABOR_DAY, BR)
    assert result.schedule.schedule_type == ScheduleType.HOLIDAY
    assert result.sample


def test_row_16_lite_lunch_has_hours_but_no_menu(readonly_dsn: str) -> None:
    assert menu(readonly_dsn, MON, LL) == MenuUnavailable(
        DaySchedule(MON, ScheduleType.WEEKDAY), LL, UnavailableReason.LITE_LUNCH
    )
    assert hours(readonly_dsn, MON, LL) == (time(14), time(15))


def test_row_17_no_wings(readonly_dsn: str) -> None:
    result = food(readonly_dsn, MON, "wings")
    assert result.matches == ()
    assert result.searched_meals == (B, L, D)


def test_row_18_onion_rings_at_monday_lunch(readonly_dsn: str) -> None:
    assert food(readonly_dsn, MON, "onion rings").matches == (
        FoodMatch(L, "Grill / sandwich", "Onion Rings"),
    )


def test_row_19_no_beef_patty_at_friday_lunch(readonly_dsn: str) -> None:
    assert food(readonly_dsn, FRI, "beef patty", L).matches == ()
    assert food(readonly_dsn, MON, "beef patty", L).matches == (
        FoodMatch(L, "Grill / sandwich", "Beef Patty"),
    )


def test_row_33_monday_dinner(readonly_dsn: str) -> None:
    assert meal_menu(readonly_dsn, MON, D).stations == (
        StationMenu(
            "Dinner / turntable",
            (
                "Herb-Roasted Chicken",
                "Seasoned Rice",
                "Steamed Green Beans",
                "Roasted Sweet Potatoes",
            ),
        ),
    )


@pytest.mark.parametrize(
    ("day", "meal"),
    [(MON, meal) for meal in (B, L, LL, D)]
    + [(day, meal) for day in (SAT, THANKSGIVING, LABOR_DAY) for meal in (BR, D)],
)
def test_every_served_meal_has_hours(readonly_dsn: str, day: date, meal: MealType) -> None:
    result = on(readonly_dsn, day, lambda r, s: get_meal_hours(r, s, meal))
    assert not isinstance(result, HoursUnavailable)


async def _all_food_items(repository: PostgresRepository) -> set[str]:
    items: set[str] = set()
    for meal in MealType:
        for weekday in range(1, 8):
            items |= {
                i.food_item for i in await repository.get_menu(MenuScope.WEEKLY, weekday, meal)
            }
        items |= {
            i.food_item for i in await repository.get_menu(MenuScope.HOLIDAY_SAMPLE, None, meal)
        }
    return items


# Spec section 9.2, with the 9.3 synonyms applied.
SPEC_9_2 = {
    "wings": set(),
    "onion rings": {"Onion Rings"},
    "mac": {"THS Baked Mac & Cheese"},
    "mac and cheese": {"THS Baked Mac & Cheese"},
    "mac & cheese": {"THS Baked Mac & Cheese"},
    "hot dogs": {"All Beef Hot Dog"},
    "pancakes": {"Blueberry Pancakes", "Buttermilk Pancake Mix", "Maple Pancakes", "Pancake"},
    "tacos": {"Taco Bar"},
    "potato": {
        "Candied Sweet Potato",
        "Mashed Potatoes",
        "Roasted Red Potatoes",
        "Roasted Sweet Potatoes",
        "Roasted Yellow Potatoes",
    },
    "ham": set(),
    "burgers": {"Beef Patty", "Turkey Patty", "Veggie Burger"},
    "hamburger": {"Beef Patty", "Turkey Patty", "Veggie Burger"},
    "fries": {"French Fries"},
    "eggs": {"Scrambled Eggs", "Scrambled Eggs with Cheese", "Butter Egg Noodle"},
    "greens": {"Vegetarian Collard Greens", "Steamed Green Beans", "Western Green Beans"},
    "veggies": {"Veggie Sausage Patty", "Veggie Burger"},
    "sausages": {
        "Pork Sausage Link",
        "Pork Sausage Patty",
        "Turkey Sausage",
        "Turkey Sausage Patty",
        "Veggie Sausage Patty",
    },
    "hash brown": {"Hash Brown Patty", "Hashbrowns"},
    "hashbrowns": {"Hash Brown Patty", "Hashbrowns"},
}


def test_spec_9_2_results_against_the_whole_dataset(readonly_dsn: str) -> None:
    items = with_repository(readonly_dsn, _all_food_items)
    assert len(items) > 90
    for keyword, expected in SPEC_9_2.items():
        query = compile_query(keyword)
        assert {item for item in items if query.matches(item)} == expected, keyword
