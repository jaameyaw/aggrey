"""Food matching (spec section 9). Code must not add rules or synonyms not written there (N-17).

Matching is on whole words, never substrings, so "ham" does not match "Hamburger Bun".
"""

from collections.abc import Sequence
from dataclasses import dataclass

from aggrey.domain.text import words

# Spec 9.3, keyed on the keyword after the singular step (9.1 step 3). Each value
# lists the alternatives; an item matching any one of them counts.
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "mac n cheese": ("mac and cheese",),
    "mac n chz": ("mac and cheese",),
    "mac and chz": ("mac and cheese",),
    "hashbrown": ("hash brown", "hashbrown"),
    "hash brown": ("hash brown", "hashbrown"),
    "hotdog": ("hot dog",),
}
# The burger entry matches only items with exactly these words, and never a bun.
_BURGER_KEYS = frozenset({"burger", "hamburger"})
_BURGER_ITEMS = ("beef patty", "turkey patty", "veggie burger")


def singular_forms(word: str) -> frozenset[str]:
    """Spec 9.1 step 3. "ies" words have two forms (fries: fry or frie)."""
    if len(word) > 4 and word.endswith("ies"):
        return frozenset({word[:-3] + "y", word[:-1]})
    if word.endswith(("oes", "xes", "zes", "ches", "shes")):
        return frozenset({word[:-2]})
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return frozenset({word[:-1]})
    return frozenset({word})


@dataclass(frozen=True, slots=True)
class _Alternative:
    # The singular forms of each keyword word.
    words: tuple[frozenset[str], ...]
    # The item must have exactly these words and no others (the burger entry).
    exact: bool = False

    def matches(self, item_words: Sequence[frozenset[str]]) -> bool:
        item_forms = frozenset().union(*item_words)
        if not all(forms & item_forms for forms in self.words):
            return False
        if not self.exact:
            return True
        keyword_forms = frozenset().union(*self.words)
        return len(item_words) == len(self.words) and all(
            forms & keyword_forms for forms in item_words
        )


@dataclass(frozen=True, slots=True)
class FoodQuery:
    keyword: str
    alternatives: tuple[_Alternative, ...]
    # Spec 9.3 exclusions.
    exclude_buns: bool = False
    # A keyword with "fries" only matches items whose name has the word "fries".
    required_word: str | None = None

    def matches(self, food_item: str) -> bool:
        item = words(food_item)
        if not item:
            return False
        if self.required_word is not None and self.required_word not in item:
            return False
        item_words = [singular_forms(word) for word in item]
        if self.exclude_buns and "bun" in item_words[-1]:
            return False
        return any(alternative.matches(item_words) for alternative in self.alternatives)


def compile_query(keyword: str) -> FoodQuery:
    """Build the matcher for a food keyword (already stripped of filler words by M6)."""
    raw = words(keyword)
    if not raw:
        raise ValueError("food keyword is empty")
    key = " ".join(_primary_form(word) for word in raw)
    required_word = "fries" if "fries" in raw else None
    if key in _BURGER_KEYS:
        alternatives = tuple(_alternative(item, exact=True) for item in _BURGER_ITEMS)
        return FoodQuery(" ".join(raw), alternatives, exclude_buns=True)
    targets = _SYNONYMS.get(key)
    if targets is None:
        alternatives = (_Alternative(tuple(singular_forms(word) for word in raw)),)
    else:
        alternatives = tuple(_alternative(target) for target in targets)
    return FoodQuery(" ".join(raw), alternatives, required_word=required_word)


def _alternative(text: str, *, exact: bool = False) -> _Alternative:
    return _Alternative(tuple(singular_forms(word) for word in text.split()), exact=exact)


def _primary_form(word: str) -> str:
    # One spelling per word for the synonym lookup; "ies" words use the "y" form.
    return min(singular_forms(word), key=lambda form: (not form.endswith("y"), form))
