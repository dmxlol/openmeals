from core.config import settings
from libs.locale import Locale, parse_tags


class AcceptLanguageParser:
    def __init__(self, default_locale: str) -> None:
        self._default = Locale(default_locale)
        self._by_tag: dict[str, Locale] = {loc.value.lower(): loc for loc in Locale}

    def __call__(self, header: str) -> Locale:
        for lang, _ in parse_tags(header):
            if locale := self._by_tag.get(lang.lower()):
                return locale
        return self._default


accept_language_parser = AcceptLanguageParser(settings.default_locale)
