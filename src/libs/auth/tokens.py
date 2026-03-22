import secrets
import typing as t
from datetime import timedelta

from authlib.jose import jwt
from authlib.jose.errors import JoseError

from libs.datetime import utcnow
from libs.exceptions import UnauthorizedError

if t.TYPE_CHECKING:
    from core.config import Settings


class TokenPair(t.TypedDict):
    access_token: str
    refresh_token: str
    token_type: str


class TokenProvider(t.Protocol):
    def create_access_token(self, sub: str, name: str) -> str: ...
    def create_refresh_token(self, sub: str, name: str) -> str: ...
    def create_token_pair(self, sub: str, name: str) -> TokenPair: ...
    def decode_token(self, token: str, expected_type: str) -> dict: ...


ISS = "openmeals"
AUD = "openmeals-api"


class JWTTokenProvider:
    def __init__(self, settings: "Settings") -> None:
        self._key = settings.secret_key.get_secret_value()
        self._alg = settings.jwt_algorithm
        self._access_ttl = timedelta(minutes=settings.access_token_expire_minutes)
        self._refresh_ttl = timedelta(days=settings.refresh_token_expire_days)

    def _token_factory(self, sub: str, name: str, type_: t.Literal["access", "refresh"]) -> dict:
        now = utcnow()
        exp = now + (self._access_ttl if type_ == "access" else self._refresh_ttl)
        return {
            "sub": sub,
            "name": name,
            "type": type_,
            "iss": ISS,
            "aud": AUD,
            "iat": now,
            "exp": exp,
            "jti": secrets.token_urlsafe(16),
        }

    def create_access_token(self, sub: str, name: str) -> str:
        return self._encode(self._token_factory(sub, name, "access"))

    def create_refresh_token(self, sub: str, name: str) -> str:
        return self._encode(self._token_factory(sub, name, "refresh"))

    def create_token_pair(self, sub: str, name: str) -> TokenPair:
        return {
            "access_token": self.create_access_token(sub, name),
            "refresh_token": self.create_refresh_token(sub, name),
            "token_type": "bearer",
        }

    def decode_token(self, token: str, expected_type: str) -> dict:
        try:
            payload = jwt.decode(token, self._key, claims_options={"iss": {"value": ISS}, "aud": {"value": AUD}})
            payload.validate()
        except JoseError as e:
            raise UnauthorizedError from e
        if payload.get("type") != expected_type:
            raise UnauthorizedError
        return dict(payload)

    def _encode(self, payload: dict) -> str:
        return jwt.encode({"alg": self._alg}, payload, self._key).decode()
