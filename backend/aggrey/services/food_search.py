"""Food lookup (spec 7.4 steps 2-5 and section 9; schema doc section 12).

No match means "not on the menu I have", never "not served" (schema doc section 13).
The station-alias fallback (7.4 step 7) and the finished-meal reply (N-44) are M6's.
"""

from dataclasses import dataclass

from aggrey.adapters.repository import DiningRepository
from aggrey.domain.food_match import compile_query
from aggrey.domain.meals import meals_served
from aggrey.domain.models import MealType, MenuScope
from aggrey.domain.schedule import DaySchedule
from aggrey.services.menu import menu_source


@dataclass(frozen=True, slots=True)
class FoodMatch:
    meal: MealType
    station: str
    food_item: str


@dataclass(frozen=True, slots=True)
class FoodSearch:
    schedule: DaySchedule
    keyword: str
    # Meals searched, in schedule order. Lite Lunch has no menu and is never searched.
    searched_meals: tuple[MealType, ...]
    # Grouped by meal (schedule order), then station, then display order.
    matches: tuple[FoodMatch, ...]
    # The meal the student named, when that meal isn't served that day (7.4 step 3).
    meal_not_served: MealType | None
    # True for the holiday and break sample menus (6.5).
    sample: bool


async def search_food(
    repository: DiningRepository,
    schedule: DaySchedule,
    keyword: str,
    meal: MealType | None = None,
) -> FoodSearch:
    query = compile_query(keyword)
    served = meals_served(schedule.schedule_type)
    meal_not_served = meal if meal is not None and meal not in served else None
    wanted = served if meal is None or meal_not_served is not None else (meal,)
    searched = tuple(m for m in wanted if m != MealType.LITE_LUNCH)

    scope, weekday = menu_source(schedule)
    matches: list[FoodMatch] = []
    for searched_meal in searched:
        for item in await repository.get_menu(scope, weekday, searched_meal):
            if query.matches(item.food_item):
                matches.append(FoodMatch(searched_meal, item.station, item.food_item))
    return FoodSearch(
        schedule,
        query.keyword,
        searched,
        tuple(matches),
        meal_not_served,
        sample=scope == MenuScope.HOLIDAY_SAMPLE,
    )
