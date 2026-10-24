"""Users, roles, and the input rules for credentials. Pure: no I/O, no hashing, no tokens."""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.errors import InvalidRequestError

EMAIL_MAX_LENGTH = 254
PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 128

_EMAIL_SHAPE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Role(StrEnum):
    USER = "user"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class User:
    user_id: str
    email: str  # always stored normalized (lower-case, trimmed)
    password_hash: str
    role: Role
    is_active: bool
    created_at: datetime


def normalize_email(raw: str) -> str:
    """Trim and lower-case. Deliberately conservative: a shape check, not full RFC validation."""
    email = raw.strip().lower()
    if len(email) > EMAIL_MAX_LENGTH or not _EMAIL_SHAPE.match(email):
        raise InvalidRequestError(
            f"invalid email shape: {email[:40]!r}", public_message="Enter a valid email address."
        )
    return email


def validate_password(password: str) -> None:
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise InvalidRequestError(
            "password length out of range",
            public_message=(
                f"The password must be {PASSWORD_MIN_LENGTH} to {PASSWORD_MAX_LENGTH} characters."
            ),
        )
