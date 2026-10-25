"""Engine and session factory. Created once at startup by the container, closed at shutdown."""

from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.adapters.db.postgres.tables import assessments, users
from app.core.config import ConfigurationError


def create_engine(*, url: str, pool_size: int, max_overflow: int) -> AsyncEngine:
    # pool_pre_ping: a connection the database dropped is replaced instead of failing a request.
    return create_async_engine(
        url, pool_size=pool_size, max_overflow=max_overflow, pool_pre_ping=True
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False: rows are converted to domain objects and never reused as ORM state.
    return async_sessionmaker(engine, expire_on_commit=False)


async def verify_schema(engine: AsyncEngine) -> None:
    """Fail at startup, with an actionable message, if the database is unreachable or unmigrated."""
    try:
        async with engine.connect() as connection:
            await connection.execute(select(users.c.user_id).limit(1))
            await connection.execute(select(assessments.c.assessment_id).limit(1))
    except ProgrammingError as exc:
        raise ConfigurationError(
            "the database schema is missing or outdated; run `alembic upgrade head`"
        ) from exc
    except (SQLAlchemyError, OSError) as exc:
        raise ConfigurationError(f"cannot reach the database: {exc!r}") from exc
