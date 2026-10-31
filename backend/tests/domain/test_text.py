import pytest

from aggrey.domain.text import normalize, words


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("What's for Dinner?", "whats for dinner"),
        ("what\N{RIGHT SINGLE QUOTATION MARK}s for lunch", "whats for lunch"),  # curly apostrophe
        ("\N{LEFT DOUBLE QUOTATION MARK}mac\N{RIGHT DOUBLE QUOTATION MARK}", "mac"),
        ("Mac & Cheese", "mac and cheese"),
        ("mac&cheese", "mac and cheese"),
        ("Grill / sandwich", "grill sandwich"),
        ("Main hot-food", "main hot food"),
        ("lunch on 11/25?", "lunch on 11/25"),
        ("dinner 11-25", "dinner 11-25"),
        ("11/ 25", "11 25"),
        ("-5", "5"),
        ("  lots   of\tspace\n", "lots of space"),
        ("!!!", ""),
        ("", ""),
    ],
)
def test_normalize(text: str, expected: str) -> None:
    assert normalize(text) == expected


def test_words() -> None:
    assert words("What's at the Grill / sandwich?") == ["whats", "at", "the", "grill", "sandwich"]
    assert words("?!") == []
