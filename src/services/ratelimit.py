import base64
import json
import typing as t

from authlib.jose import jwt as jose_jwt
from authlib.jose.errors import JoseError
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings
from libs.auth.tokens import AUD, JWTTokenProvider

tokens = JWTTokenProvider(settings)


def get_real_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else ""


def decode_unverified_payload(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:  # noqa: PLR2004
        return {}
    try:
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception:
        return {}


def resolve_client_brand(token: str) -> str | None:
    payload = decode_unverified_payload(token)
    iss = payload.get("iss")
    if not iss or iss not in settings.clients:
        return None
    try:
        claims = jose_jwt.decode(token, settings.clients[iss], claims_options={"aud": {"value": AUD}})
        claims.validate()
        return str(iss)
    except (JoseError, Exception):
        return None


def resolve_brand(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        payload = decode_unverified_payload(auth[7:])
        azp = payload.get("azp")
        if azp:
            return str(azp)

    client_token = request.headers.get("Client-Token") or request.cookies.get("client_token")
    if client_token:
        brand = resolve_client_brand(client_token)
        if brand:
            return brand

    return "unknown"


class LimiterKeyFunc(t.Protocol):
    def __call__(self, request: Request) -> str: ...


class RateLimitWhitelist(t.Protocol):
    def should_whitelist(self, request: Request) -> bool: ...


class RemoteAddressWhitelist:
    allowed_ips: t.ClassVar[frozenset[str]] = frozenset(settings.allowed_ips)

    def should_whitelist(self, request: Request) -> bool:
        return get_real_ip(request) in self.allowed_ips


class UserIdExtractor:
    """Returns user_id (sub) for authenticated requests, empty string otherwise."""

    def __call__(self, request: Request) -> str:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return ""
        try:
            return tokens.decode_token(auth[7:], "access")["sub"]
        except Exception:
            return ""


class AnonymousAddressExtractor:
    """Returns real IP for anonymous requests, empty string for authenticated."""

    def __call__(self, request: Request) -> str:
        if request.headers.get("Authorization"):
            return ""
        return get_real_ip(request)


class DefaultRateLimitStrategy:
    whitelists: t.ClassVar[list[RateLimitWhitelist]] = [RemoteAddressWhitelist()]

    def __init__(self, extractor: LimiterKeyFunc) -> None:
        self.extractor = extractor

    def __call__(self, request: Request) -> str:
        for wl in self.whitelists:
            if wl.should_whitelist(request):
                return ""
        key = self.extractor(request)
        if not key:
            return ""
        return f"{resolve_brand(request)}:{key}"


def brand_limit(known: str, unknown: str) -> t.Callable[[str], str]:
    def get(key: str) -> str:
        brand = key.split(":", maxsplit=1)[0] if ":" in key else "unknown"
        return known if brand != "unknown" else unknown

    return get


limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url, headers_enabled=True)
user_limit_strategy = DefaultRateLimitStrategy(UserIdExtractor())
ip_limit_strategy = DefaultRateLimitStrategy(AnonymousAddressExtractor())
