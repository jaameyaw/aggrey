"""Date resolution (spec sections 3.2 and 6.1, roadmap N-12 and N-13).

Works on the words of an already normalized message (spec section 2); normalizing the
text is the conversation layer's job. The current time is always passed in.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from itertools import pairwise
from zoneinfo import ZoneInfo

TODAY_WORDS = frozenset({"today"})
TONIGHT_WORDS = frozenset({"tonight"})
TOMORROW_WORDS = frozenset({"tomorrow", "tmrw", "tmr", "tomorow"})

# ISO weekday numbers (1 = Monday ... 7 = Sunday). Owner decision, 2026-10-27.
WEEKDAY_WORDS: dict[str, int] = {
    "monday": 1,
    "mon": 1,
    "tuesday": 2,
    "tue": 2,
    "tues": 2,
    "wednesday": 3,
    "wed": 3,
    "weds": 3,
    "thursday": 4,
    "thu": 4,
    "thur": 4,
    "thurs": 4,
    "friday": 5,
    "fri": 5,
    "saturday": 6,
    "sat": 6,
    "sunday": 7,
    "sun": 7,
}

UNSUPPORTED_WORDS = frozenset({"yesterday", "weekend"})
UNSUPPORTED_PHRASES = (
    ("last", "night"),
    ("next", "week"),
    ("this", "week"),
    ("this", "weekend"),
)

# "may" is left out: it counts as a month only next to a number (spec 3.2).
MONTH_WORDS = frozenset(
    {
        "january",
        "jan",
        "february",
        "feb",
        "march",
        "mar",
        "april",
        "apr",
        "june",
        "jun",
        "july",
        "jul",
        "august",
        "aug",
        "september",
        "sep",
        "sept",
        "october",
        "oct",
        "november",
        "nov",
        "december",
        "dec",
    }
)

_NUMERIC_DATE = re.compile(r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?")
_NUMBER = re.compile(r"\d+(?:st|nd|rd|th)?")


@dataclass(frozen=True, slots=True)
class ResolvedDate:
    day: date
    # "tonight" was used; the meal is dinner when the message names no meal.
    implies_dinner: bool = False


class UnrecognizedReason(StrEnum):
    UNSUPPORTED = "unsupported"
    CONFLICTING = "conflicting"


@dataclass(frozen=True, slots=True)
class UnrecognizedDate:
    """The date can't be answered; ask the student to rephrase. Never guess a date."""

    reason: UnrecognizedReason


def to_local(now: datetime, tz: ZoneInfo) -> datetime:
    """`now` in the college timezone. Naive datetimes are rejected."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return now.astimezone(tz)


def next_weekday(today: date, iso_weekday: int) -> date:
    """The next day with this weekday name: today if it matches, never a past date."""
    return today + timedelta(days=(iso_weekday - today.isoweekday()) % 7)


def has_unsupported_date(words: Sequence[str]) -> bool:
    for index, word in enumerate(words):
        if word in UNSUPPORTED_WORDS or word in MONTH_WORDS or _NUMERIC_DATE.fullmatch(word):
            return True
        if word == "may" and _next_to_number(words, index):
            return True
    pairs = set(pairwise(words))
    return any(phrase in pairs for phrase in UNSUPPORTED_PHRASES)


def resolve_date(
    words: Sequence[str], now: datetime, tz: ZoneInfo
) -> ResolvedDate | UnrecognizedDate:
    """The calendar date a message asks about. No date phrase means today (N-12)."""
    if has_unsupported_date(words):
        return UnrecognizedDate(UnrecognizedReason.UNSUPPORTED)

    today = to_local(now, tz).date()
    days: set[date] = set()
    implies_dinner = False
    for word in words:
        if word in TODAY_WORDS:
            days.add(today)
        elif word in TONIGHT_WORDS:
            days.add(today)
            implies_dinner = True
        elif word in TOMORROW_WORDS:
            days.add(today + timedelta(days=1))
        elif word in WEEKDAY_WORDS:
            days.add(next_weekday(today, WEEKDAY_WORDS[word]))

    if len(days) > 1:
        return UnrecognizedDate(UnrecognizedReason.CONFLICTING)
    day = days.pop() if days else today
    return ResolvedDate(day, implies_dinner=implies_dinner)


def _next_to_number(words: Sequence[str], index: int) -> bool:
    neighbours = [*words[max(index - 1, 0) : index], *words[index + 1 : index + 2]]
    return any(_NUMBER.fullmatch(word) for word in neighbours)
