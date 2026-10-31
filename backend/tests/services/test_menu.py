import pytest

from aggrey.domain.models import MealType, MenuScope
from aggrey.domain.schedule import DaySchedule
from aggrey.services.menu import (
    MealMenu,
    MenuUnavailable,
    StationMenu,
    StationNotFound,
    UnavailableReason,
    get_meal_menu,
    menu_source,
)
from tests.conftest import run
from tests.services.fakes import MONDAY, SATURDAY, THANKSGIVING, RecordingRepository


def test_menu_source() -> None:
    assert menu_source(MONDAY) == (MenuScope.WEEKLY, 1)
    assert menu_source(SATURDAY) == (MenuScope.WEEKLY, 6)
    assert menu_source(THANKSGIVING) == (MenuScope.HOLIDAY_SAMPLE, None)


def test_full_meal_grouped_by_station_alphabetically_items_in_display_order() -> None:
    result = run(get_meal_menu(RecordingRepository(), MONDAY, MealType.LUNCH))
    assert result == MealMenu(
        MONDAY,
        MealType.LUNCH,
        (
            StationMenu("Grill / sandwich", ("Beef Patty", "Onion Rings")),
            StationMenu("Main hot-food", ("BBQ Chicken",)),
            StationMenu("Pizza", ("Cheese Pizza", "Pepperoni Pizza")),
        ),
        sample=False,
    )


@pytest.mark.parametrize(
    "station", ["Pizza", "pizza", " PIZZA ", "Grill / sandwich", "grill sandwich"]
)
def test_station_name_matches_after_normalization(station: str) -> None:
    result = run(get_meal_menu(RecordingRepository(), MONDAY, MealType.LUNCH, station))
    assert isinstance(result, MealMenu)
    assert len(result.stations) == 1


def test_station_not_on_that_meal_lists_the_stations_that_are() -> None:
    result = run(get_meal_menu(RecordingRepository(), MONDAY, MealType.LUNCH, "Pasta"))
    assert result == StationNotFound(
        MONDAY, MealType.LUNCH, "Pasta", ("Grill / sandwich", "Main hot-food", "Pizza")
    )


def test_lite_lunch_has_no_menu_and_is_never_queried() -> None:
    repository = RecordingRepository()
    result = run(get_meal_menu(repository, MONDAY, MealType.LITE_LUNCH))
    assert result == MenuUnavailable(MONDAY, MealType.LITE_LUNCH, UnavailableReason.LITE_LUNCH)
    assert repository.menu_calls == []


def test_zero_rows_is_unavailable_never_another_day() -> None:
    repository = RecordingRepository(menus=[])
    result = run(get_meal_menu(repository, MONDAY, MealType.DINNER))
    assert result == MenuUnavailable(MONDAY, MealType.DINNER, UnavailableReason.NO_ROWS)
    assert repository.menu_calls == [(MenuScope.WEEKLY, 1, MealType.DINNER)]


@pytest.mark.parametrize("meal", [MealType.BRUNCH, MealType.DINNER])
def test_break_day_reads_only_the_holiday_sample(meal: MealType) -> None:
    repository = RecordingRepository()
    result = run(get_meal_menu(repository, THANKSGIVING, meal))
    assert isinstance(result, MealMenu)
    assert result.sample
    assert repository.menu_calls == [(MenuScope.HOLIDAY_SAMPLE, None, meal)]
    items = [item for station in result.stations for item in station.items]
    # Never Wednesday's weekly dinner and never Saturday's weekly brunch (N-16, 6.6).
    assert "Wednesday Meatloaf" not in items
    assert "Saturday Waffle" not in items


def test_weekend_brunch_reads_the_weekly_saturday_rows() -> None:
    result = run(get_meal_menu(RecordingRepository(), SATURDAY, MealType.BRUNCH))
    assert isinstance(result, MealMenu)
    assert not result.sample
    assert result.stations == (StationMenu("Grill / sandwich", ("Saturday Waffle",)),)


@pytest.mark.parametrize(
    ("schedule", "meal"),
    [(SATURDAY, MealType.LUNCH), (THANKSGIVING, MealType.BREAKFAST), (MONDAY, MealType.BRUNCH)],
)
def test_meal_not_served_is_a_caller_error(schedule: DaySchedule, meal: MealType) -> None:
    with pytest.raises(ValueError, match="not served"):
        run(get_meal_menu(RecordingRepository(), schedule, meal))
