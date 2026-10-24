"""One place that turns database failures into the application's `PersistenceError`."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.exc import SQLAlchemyError

from app.domain.errors import PersistenceError


@contextmanager
def database_errors(action: str) -> Iterator[None]:
    """Wrap driver and connection failures; the original exception stays as `__cause__`.

    `OSError` covers connection-level failures (refused, reset, timed out) that some drivers
    raise without wrapping them in a SQLAlchemy error.
    """
    try:
        yield
    except (SQLAlchemyError, OSError) as exc:
        raise PersistenceError(f"database error while {action}: {exc!r}") from exc
