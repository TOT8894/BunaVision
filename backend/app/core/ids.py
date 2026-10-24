"""Identifier generation."""

import uuid


def new_assessment_id() -> str:
    """Full 128-bit random id. Not truncated: truncation only raises the collision odds."""
    return f"asmt_{uuid.uuid4().hex}"


def new_user_id() -> str:
    """Random UUID string; also the primary key type the database uses for users."""
    return str(uuid.uuid4())
