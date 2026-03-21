import enum
import typing as t

from libs.auth.local import LocalProvider
from libs.exceptions import UnauthorizedError

if t.TYPE_CHECKING:
    from core.config import Settings


class OAuthProviderName(enum.StrEnum):
    LOCAL = "local"


class OAuthClaims(t.TypedDict):
    sub: str
    email: str
    name: str


class OAuthProvider(t.Protocol):
    def encode(self, claims: OAuthClaims, settings: "Settings") -> str: ...
    def decode(self, code: str, settings: "Settings") -> OAuthClaims: ...


def get_provider(name: OAuthProviderName) -> OAuthProvider:
    match name:
        case OAuthProviderName.LOCAL:
            return LocalProvider()
        case _:
            raise UnauthorizedError
