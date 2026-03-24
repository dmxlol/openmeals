from enum import StrEnum


class Locale(StrEnum):
    EN_US = "en-US"
    UK_UA = "uk-UA"


def parse_tags(header: str) -> list[tuple[str, float]]:
    """Parse Accept-Language header into (lang, quality) pairs sorted by quality."""
    tags: list[tuple[str, float]] = []
    for part in header.split(","):
        lang, _, q_part = part.strip().partition(";q=")
        try:
            quality = float(q_part) if q_part else 1.0
        except ValueError:
            quality = 1.0
        tags.append((lang.strip(), quality))
    tags.sort(key=lambda x: -x[1])
    return tags
