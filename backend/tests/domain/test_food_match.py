import pytest

from aggrey.domain.food_match import compile_query, singular_forms


@pytest.mark.parametrize(
    ("word", "forms"),
    [
        ("fries", {"fry", "frie"}),
        ("veggies", {"veggy", "veggie"}),
        ("pies", {"pie"}),  # 4 letters: not the "ies" rule, plain "s"
        ("potatoes", {"potato"}),
        ("boxes", {"box"}),
        ("sandwiches", {"sandwich"}),
        ("dishes", {"dish"}),
        ("sausages", {"sausage"}),  # "ses" is not in the "es" list
        ("cheeses", {"cheese"}),
        ("wings", {"wing"}),
        ("swiss", {"swiss"}),
        ("bus", {"bus"}),  # 3 letters
        ("egg", {"egg"}),
    ],
)
def test_singular_forms(word: str, forms: set[str]) -> None:
    assert singular_forms(word) == forms


def matching(keyword: str, items: list[str]) -> list[str]:
    query = compile_query(keyword)
    return [item for item in items if query.matches(item)]


def test_whole_words_not_substrings() -> None:
    assert matching("ham", ["White Hamburger Bun", "Ham Steak"]) == ["Ham Steak"]


def test_every_keyword_word_must_appear_in_any_order() -> None:
    items = ["Onion Rings", "Fried Onion", "Ring Pop"]
    assert matching("onion rings", items) == ["Onion Rings"]
    assert matching("rings onion", items) == ["Onion Rings"]


def test_plural_keyword_matches_singular_item_and_back() -> None:
    assert matching("pancakes", ["Pancake", "Maple Pancakes"]) == ["Pancake", "Maple Pancakes"]
    assert matching("pancake", ["Pancake", "Maple Pancakes"]) == ["Pancake", "Maple Pancakes"]


def test_ie_form_matches_veggie() -> None:
    assert matching("veggies", ["Veggie Burger", "Vegetable Soup"]) == ["Veggie Burger"]


def test_ampersand_is_and() -> None:
    assert matching("mac & cheese", ["THS Baked Mac & Cheese"]) == ["THS Baked Mac & Cheese"]


@pytest.mark.parametrize("keyword", ["mac n cheese", "mac n chz", "mac and chz", "Mac & Cheese"])
def test_mac_and_cheese_synonyms(keyword: str) -> None:
    assert matching(keyword, ["THS Baked Mac & Cheese", "Mac Salad"]) == ["THS Baked Mac & Cheese"]


@pytest.mark.parametrize("keyword", ["hashbrown", "hashbrowns", "hash browns", "hash brown"])
def test_hash_brown_synonyms_match_both_spellings(keyword: str) -> None:
    assert matching(keyword, ["Hash Brown Patty", "Hashbrowns", "Brown Rice"]) == [
        "Hash Brown Patty",
        "Hashbrowns",
    ]


@pytest.mark.parametrize("keyword", ["hotdog", "hotdogs", "hot dogs"])
def test_hot_dog_synonyms(keyword: str) -> None:
    assert matching(keyword, ["All Beef Hot Dog", "Hot Wings"]) == ["All Beef Hot Dog"]


@pytest.mark.parametrize("keyword", ["burger", "burgers", "hamburger", "hamburgers"])
def test_burger_matches_patties_and_veggie_burger_only(keyword: str) -> None:
    items = [
        "Beef Patty",
        "Turkey Patty",
        "Veggie Burger",
        "Turkey Sausage Patty",
        "White Hamburger Bun",
        "Veggie Burger Bun",
    ]
    assert matching(keyword, items) == ["Beef Patty", "Turkey Patty", "Veggie Burger"]


def test_fries_never_matches_stir_fry() -> None:
    items = ["French Fries", "Orange Chicken Stir Fry"]
    assert matching("fries", items) == ["French Fries"]
    assert matching("french fries", items) == ["French Fries"]
    # "fry" is not the excluded keyword.
    assert matching("fry", items) == items


def test_no_wings_synonym() -> None:
    assert matching("wings", ["Buffalo Chicken Pasta", "BBQ Chicken"]) == []


def test_keyword_is_normalized() -> None:
    assert compile_query("  Onion RINGS! ").keyword == "onion rings"


def test_empty_keyword_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        compile_query(" ?! ")


def test_empty_item_never_matches() -> None:
    assert not compile_query("egg").matches("!!")
