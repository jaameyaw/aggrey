from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from aggrey.domain.dates import (
    WEEKDAY_WORDS,
    ResolvedDate,
    UnrecognizedDate,
    UnrecognizedReason,
    next_weekday,
    resolve_date,
    to_local,
)

NY = ZoneInfo("America/New_York")
# Monday 2026-10-26, 08:00 in New York.
MONDAY_8AM = datetime(2026, 10, 26, 8, tzinfo=NY)

UNSUPPORTED = UnrecognizedDate(UnrecognizedReason.UNSUPPORTED)
CONFLICTING = UnrecognizedDate(UnrecognizedReason.CONFLICTING)


def resolve(text: str, now: datetime = MONDAY_8AM) -> ResolvedDate | UnrecognizedDate:
    return resolve_date(text.split(), now, NY)


def test_no_date_phrase_is_today() -> None:
    assert resolve("whats for dinner") == ResolvedDate(date(2026, 10, 26))


def test_today() -> None:
    assert resolve("whats for lunch today") == ResolvedDate(date(2026, 10, 26))


def test_tonight_is_today_and_implies_dinner() -> None:
    assert resolve("whats for tonight") == ResolvedDate(date(2026, 10, 26), implies_dinner=True)


@pytest.mark.parametrize("word", ["tomorrow", "tmrw", "tmr", "tomorow"])
def test_tomorrow_spellings(word: str) -> None:
    assert resolve(f"lunch {word}") == ResolvedDate(date(2026, 10, 27))


@pytest.mark.parametrize(("word", "iso"), sorted(WEEKDAY_WORDS.items()))
def test_weekday_words_resolve_to_the_next_day_with_that_name(word: str, iso: int) -> None:
    result = resolve(f"lunch {word}")
    assert isinstance(result, ResolvedDate)
    assert result.day.isoweekday() == iso
    assert date(2026, 10, 26) <= result.day <= date(2026, 11, 1)


def test_weekday_word_naming_today_is_today() -> None:
    assert resolve("lunch monday") == ResolvedDate(date(2026, 10, 26))


def test_weekday_word_is_never_a_past_date() -> None:
    sunday = datetime(2026, 11, 1, 12, tzinfo=NY)
    assert resolve("lunch sat", sunday) == ResolvedDate(date(2026, 11, 7))
    assert resolve("lunch fri", sunday) == ResolvedDate(date(2026, 11, 6))


def test_plural_weekday_is_not_a_date_word() -> None:
    assert resolve("lunch mondays") == ResolvedDate(date(2026, 10, 26))


def test_next_weekday() -> None:
    assert next_weekday(date(2026, 10, 26), 1) == date(2026, 10, 26)
    assert next_weekday(date(2026, 10, 27), 1) == date(2026, 11, 2)


@pytest.mark.parametrize(
    "text",
    [
        "whats for dinner 11/25",
        "whats for dinner 11-25",
        "dinner 11/25/26",
        "what was for lunch yesterday",
        "what was for dinner last night",
        "lunch next week",
        "lunch this week",
        "brunch this weekend",
        "brunch on the weekend",
        "lunch nov 25",
        "lunch november 25th",
        "dinner on dec",
        "lunch may 3",
        "lunch 3 may",
        "lunch may 3rd",
    ],
)
def test_unsupported_dates_are_never_guessed(text: str) -> None:
    assert resolve(text) == UNSUPPORTED


def test_may_without_a_number_is_not_a_date() -> None:
    assert resolve("may i see the dinner menu") == ResolvedDate(date(2026, 10, 26))


def test_unsupported_wins_over_a_supported_phrase() -> None:
    assert resolve("lunch today or yesterday") == UNSUPPORTED


def test_two_different_dates_conflict() -> None:
    assert resolve("lunch today or tomorrow") == CONFLICTING
    assert resolve("dinner friday tomorrow") == CONFLICTING


def test_two_phrases_for_the_same_day_do_not_conflict() -> None:
    assert resolve("today tonight") == ResolvedDate(date(2026, 10, 26), implies_dinner=True)
    assert resolve("lunch tuesday tomorrow") == ResolvedDate(date(2026, 10, 27))
    assert resolve("lunch monday today") == ResolvedDate(date(2026, 10, 26))


def test_naive_now_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        resolve("lunch", datetime(2026, 10, 26, 8))  # noqa: DTZ001


def test_to_local_converts_utc() -> None:
    assert to_local(datetime(2026, 10, 27, 2, tzinfo=UTC), NY) == datetime(
        2026, 10, 26, 22, tzinfo=NY
    )


def test_today_uses_new_york_not_utc() -> None:
    # Acceptance row 32: Monday 22:00 in New York is Tuesday 02:00 UTC.
    now = datetime(2026, 10, 27, 2, tzinfo=UTC)
    assert resolve("lunch", now) == ResolvedDate(date(2026, 10, 26))
    assert resolve("lunch tomorrow", now) == ResolvedDate(date(2026, 10, 27))


def test_midnight_boundary() -> None:
    before = datetime(2026, 10, 26, 23, 59, 59, tzinfo=NY)
    after = datetime(2026, 10, 27, 0, 0, tzinfo=NY)
    assert resolve("lunch tomorrow", before) == ResolvedDate(date(2026, 10, 27))
    assert resolve("lunch tomorrow", after) == ResolvedDate(date(2026, 10, 28))


@pytest.mark.parametrize(
    "utc_hour",
    [5, 6],  # 01:30 EDT and 01:30 EST on the fall-back night
)
def test_fall_back_night_stays_on_the_same_local_day(utc_hour: int) -> None:
    now = datetime(2026, 11, 1, utc_hour, 30, tzinfo=UTC)
    assert to_local(now, NY).hour == 1
    assert resolve("lunch", now) == ResolvedDate(date(2026, 11, 1))
    assert resolve("lunch tomorrow", now) == ResolvedDate(date(2026, 11, 2))


@pytest.mark.parametrize(
    ("utc", "local_day"),
    [
        (datetime(2027, 3, 14, 6, 59, tzinfo=UTC), date(2027, 3, 14)),  # 01:59 EST
        (datetime(2027, 3, 14, 7, 0, tzinfo=UTC), date(2027, 3, 14)),  # 03:00 EDT
        (datetime(2027, 3, 15, 3, 59, tzinfo=UTC), date(2027, 3, 14)),  # 23:59 EDT
        (datetime(2027, 3, 15, 4, 0, tzinfo=UTC), date(2027, 3, 15)),  # 00:00 EDT
    ],
)
def test_spring_forward_day(utc: datetime, local_day: date) -> None:
    assert resolve("lunch", utc) == ResolvedDate(local_day)
