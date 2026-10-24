"""Create an administrator account. Run by an operator; there is no HTTP route for this.

    python -m scripts.create_admin --email admin@example.com

The password is read from a prompt (or from stdin when piped), never from a command-line
argument or environment variable. Needs the same environment as the API (DATABASE_URL,
JWT_SECRET, ...) and a migrated database. To make an existing user an admin, update the
`role` column directly: that is deliberately an operator action, not an API feature.
"""

import argparse
import asyncio
import getpass
import sys

from app.adapters.db.postgres.engine import create_engine, create_session_factory, verify_schema
from app.adapters.db.postgres.user_repository import PostgresUserRepository
from app.container import build_auth_service
from app.core.clock import SystemClock
from app.core.config import get_settings
from app.domain.errors import ClientInputError


async def _create(email: str, password: str) -> str:
    settings = get_settings()
    engine = create_engine(
        url=settings.database_url.get_secret_value(),
        pool_size=1,
        max_overflow=0,
    )
    try:
        await verify_schema(engine)
        users = PostgresUserRepository(create_session_factory(engine))
        auth = build_auth_service(settings, users, SystemClock())
        admin = await auth.create_admin(email=email, password=password)
        return admin.user_id
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a BunaVision administrator.")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    if getpass.getpass("Repeat password: ") != password:
        print("Passwords do not match.", file=sys.stderr)
        return 2
    try:
        user_id = asyncio.run(_create(args.email, password))
    except ClientInputError as exc:
        print(f"Could not create the admin: {exc.public_message}", file=sys.stderr)
        return 1
    print(f"Created admin {args.email} ({user_id}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
