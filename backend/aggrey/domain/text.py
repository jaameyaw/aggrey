"""Text normalization (spec section 2). Used for messages and for food item names."""

_CURLY = str.maketrans(
    {
        "\N{LEFT SINGLE QUOTATION MARK}": "'",
        "\N{RIGHT SINGLE QUOTATION MARK}": "'",
        "\N{LEFT DOUBLE QUOTATION MARK}": '"',
        "\N{RIGHT DOUBLE QUOTATION MARK}": '"',
    }
)


def normalize(text: str) -> str:
    """Lowercase, drop apostrophes, `&` to `and`, punctuation to spaces, collapse spaces.

    `/` and `-` survive only between two digits, so dates like `11/25` stay
    recognizable (and can be rejected, spec 3.2).
    """
    text = text.lower().translate(_CURLY).replace("'", "").replace("&", " and ")
    chars = []
    for index, char in enumerate(text):
        if char.isalnum() or (char in "/-" and _between_digits(text, index)):
            chars.append(char)
        else:
            chars.append(" ")
    return " ".join("".join(chars).split())


def words(text: str) -> list[str]:
    return normalize(text).split()


def _between_digits(text: str, index: int) -> bool:
    return 0 < index < len(text) - 1 and text[index - 1].isdigit() and text[index + 1].isdigit()
