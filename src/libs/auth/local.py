import typing as t

from authlib.jose import jwt
from authlib.jose.errors import JoseError

from libs.exceptions import UnauthorizedError

if t.TYPE_CHECKING:
    from core.config import Settings
    from libs.auth.providers import OAuthClaims


class LocalProvider:
    def encode(self, claims: "OAuthClaims", settings: "Settings") -> str:
        header = {"alg": settings.jwt_algorithm}
        payload = {**claims, "type": "local_id"}
        return jwt.encode(header, payload, settings.secret_key.get_secret_value()).decode()

    def decode(self, code: str, settings: "Settings") -> "OAuthClaims":
        try:
            payload = jwt.decode(code, settings.secret_key.get_secret_value())
        except JoseError as e:
            raise UnauthorizedError from e
        if payload.get("type") != "local_id":
            raise UnauthorizedError
        return {"sub": payload["sub"], "email": payload["email"], "name": payload["name"]}
