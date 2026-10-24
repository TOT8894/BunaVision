"""Signed access tokens (JWT, HS256). Implements the `TokenIssuer` port.

A token carries only the user id, issuer and timestamps; roles and account status are always
read from the database. Expiry is checked against the injected clock (not the library's
wall clock) so behaviour is testable and consistent with the rest of the service.
"""

from typing import Any

import jwt

from app.domain.errors import AuthenticationRequiredError
from app.services.ports import Clock, IssuedToken

ISSUER = "bunavision-backend"
_ALGORITHM = "HS256"
_REQUIRED_CLAIMS = ["iss", "sub", "iat", "exp"]


class JwtTokenIssuer:
    def __init__(self, *, secret: str, ttl_s: int, clock: Clock) -> None:
        self._secret = secret
        self._ttl_s = ttl_s
        self._clock = clock

    def issue(self, user_id: str) -> IssuedToken:
        issued_at = int(self._clock.now().timestamp())
        payload: dict[str, Any] = {
            "iss": ISSUER,
            "sub": user_id,
            "iat": issued_at,
            "exp": issued_at + self._ttl_s,
        }
        token = jwt.encode(payload, self._secret, algorithm=_ALGORITHM)
        return IssuedToken(access_token=token, expires_in_s=self._ttl_s)

    def subject_of(self, token: str) -> str:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[_ALGORITHM],  # never trust the header's algorithm
                issuer=ISSUER,
                options={
                    "require": _REQUIRED_CLAIMS,
                    "verify_exp": False,  # checked below against our clock
                    "verify_iat": False,
                },
            )
        except jwt.InvalidTokenError as exc:
            raise AuthenticationRequiredError(f"token rejected: {exc}") from exc
        if int(payload["exp"]) <= int(self._clock.now().timestamp()):
            raise AuthenticationRequiredError("token expired")
        subject = payload["sub"]
        if not isinstance(subject, str):
            raise AuthenticationRequiredError("token subject is not a string")
        return subject
