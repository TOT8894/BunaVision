"""PostgreSQL implementation of the `UserRepository` port."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.db.postgres.errors import database_errors
from app.adapters.db.postgres.tables import users
from app.domain.errors import EmailAlreadyRegisteredError, PersistenceError
from app.domain.users import Role, User


class PostgresUserRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def add(self, user: User) -> None:
        statement = (
            pg_insert(users)
            .values(
                user_id=user.user_id,
                email=user.email,
                password_hash=user.password_hash,
                role=user.role.value,
                is_active=user.is_active,
                created_at=user.created_at,
            )
            # The unique index on `email` is the only conflict we translate; any other
            # integrity failure (e.g. a primary key clash) is a genuine error.
            .on_conflict_do_nothing(index_elements=[users.c.email])
            .returning(users.c.user_id)
        )
        with database_errors("adding a user"):
            async with self._sessions.begin() as session:
                inserted = (await session.execute(statement)).scalar_one_or_none()
        if inserted is None:
            raise EmailAlreadyRegisteredError(f"email already registered: {user.email}")

    async def get(self, user_id: str) -> User | None:
        return await self._fetch_one(users.c.user_id == user_id, "loading a user")

    async def find_by_email(self, email: str) -> User | None:
        return await self._fetch_one(users.c.email == email, "finding a user by email")

    async def _fetch_one(self, condition, action: str) -> User | None:  # noqa: ANN001
        with database_errors(action):
            async with self._sessions() as session:
                row = (await session.execute(select(users).where(condition))).first()
        if row is None:
            return None
        try:
            return User(
                user_id=str(row.user_id),
                email=row.email,
                password_hash=row.password_hash,
                role=Role(row.role),
                is_active=row.is_active,
                created_at=row.created_at,
            )
        except ValueError as exc:
            raise PersistenceError(f"stored user row is invalid: {exc!r}") from exc
