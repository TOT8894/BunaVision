"""Registration, login and request authentication.

Security choices worth knowing:

* Login failures are indistinguishable: an unknown email, a wrong password and a disabled
  account all raise `InvalidCredentialsError`, and an unknown email still pays the cost of a
  password check so response time does not reveal which emails exist.
* A token only names the user. The user row is loaded on every request, so disabling an
  account or changing a role takes effect immediately instead of when the token expires.
* Nothing here can create an admin from a web request. `create_admin` exists for the
  operator-run script only.
"""

import logging
from collections.abc import Callable

from app.domain.errors import AuthenticationRequiredError, InvalidCredentialsError
from app.domain.users import Role, User, normalize_email, validate_password
from app.services.ports import Clock, IssuedToken, PasswordHasher, TokenIssuer, UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenIssuer,
        clock: Clock,
        new_id: Callable[[], str],
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._clock = clock
        self._new_id = new_id

    async def register(self, *, email: str, password: str) -> User:
        return await self._create_user(email=email, password=password, role=Role.USER)

    async def create_admin(self, *, email: str, password: str) -> User:
        user = await self._create_user(email=email, password=password, role=Role.ADMIN)
        logger.info("admin account created: %s", user.user_id)
        return user

    async def login(self, *, email: str, password: str) -> IssuedToken:
        user = await self._users.find_by_email(normalize_email(email))
        # Always verify against *some* hash so unknown emails take as long as known ones.
        stored_hash = user.password_hash if user is not None else self._hasher.dummy_hash
        password_ok = await self._hasher.verify(password, stored_hash)
        if user is None or not password_ok or not user.is_active:
            raise InvalidCredentialsError("login rejected")
        return self._tokens.issue(user.user_id)

    async def authenticate(self, token: str) -> User:
        user_id = self._tokens.subject_of(token)
        user = await self._users.get(user_id)
        if user is None or not user.is_active:
            raise AuthenticationRequiredError(f"token names unknown or disabled user {user_id}")
        return user

    async def _create_user(self, *, email: str, password: str, role: Role) -> User:
        normalized = normalize_email(email)
        validate_password(password)
        user = User(
            user_id=self._new_id(),
            email=normalized,
            password_hash=await self._hasher.hash(password),
            role=role,
            is_active=True,
            created_at=self._clock.now(),
        )
        await self._users.add(user)  # raises EmailAlreadyRegisteredError on a duplicate
        return user
