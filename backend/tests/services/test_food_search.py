from aggrey.domain.models import MealType, MenuScope
from aggrey.services.food_search import FoodMatch, search_food
from tests.conftest import run
from tests.services.fakes import MONDAY, SATURDAY, THANKSGIVING, RecordingRepository

B, L, D, BR = MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER, MealType.BRUNCH


def test_searches_every_served_meal_except_lite_lunch() -> None:
    repository = RecordingRepository()
    result = run(search_food(repository, MONDAY, "onion rings"))
    assert result.searched_meals == (B, L, D)
    assert result.matches == (FoodMatch(L, "Grill / sandwich", "Onion Rings"),)
    assert result.meal_not_served is None
    assert not result.sample
    assert repository.menu_calls == [(MenuScope.WEEKLY, 1, meal) for meal in (B, L, D)]


def test_matches_are_ordered_by_meal_then_station() -> None:
    result = run(search_food(RecordingRepository(), MONDAY, "chicken"))
    assert result.matches == (
        FoodMatch(L, "Main hot-food", "BBQ Chicken"),
        FoodMatch(D, "Dinner / turntable", "Fried Chicken"),
    )


def test_named_meal_limits_the_search() -> None:
    result = run(search_food(RecordingRepository(), MONDAY, "chicken", D))
    assert result.searched_meals == (D,)
    assert result.matches == (FoodMatch(D, "Dinner / turntable", "Fried Chicken"),)


def test_named_lite_lunch_searches_nothing() -> None:
    repository = RecordingRepository()
    result = run(search_food(repository, MONDAY, "pizza", MealType.LITE_LUNCH))
    assert result.searched_meals == ()
    assert result.matches == ()
    assert repository.menu_calls == []


def test_named_meal_not_served_searches_the_meals_that_are() -> None:
    result = run(search_food(RecordingRepository(), SATURDAY, "waffle", L))
    assert result.meal_not_served == L
    assert result.searched_meals == (BR, D)
    assert result.matches == (FoodMatch(BR, "Grill / sandwich", "Saturday Waffle"),)


def test_no_match_is_empty() -> None:
    result = run(search_food(RecordingRepository(), MONDAY, "wings"))
    assert result.matches == ()
    assert result.keyword == "wings"


def test_break_day_searches_only_the_holiday_sample() -> None:
    repository = RecordingRepository()
    result = run(search_food(repository, THANKSGIVING, "waffle"))
    assert result.sample
    assert result.matches == (FoodMatch(BR, "Grill / sandwich", "Sample Waffle"),)
    assert repository.menu_calls == [(MenuScope.HOLIDAY_SAMPLE, None, meal) for meal in (BR, D)]
    assert run(search_food(repository, THANKSGIVING, "meatloaf")).matches == ()


def test_whole_word_matching_is_used() -> None:
    assert run(search_food(RecordingRepository(), MONDAY, "ham")).matches == ()
