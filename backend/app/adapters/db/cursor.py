"""Opaque pagination cursors, shared by every repository implementation.

A cursor encodes the sort position (created_at, assessment_id) of the last item on a page.
Clients treat it as an opaque string; only this module knows its shape.
"""

import base64
import binascii
import json
from datetime import datetime

from app.domain.errors import InvalidRequestError

SortKey = tuple[datetime, str]


def encode_cursor(key: SortKey) -> str:
    created_at, assessment_id = key
    payload = json.dumps({"c": created_at.isoformat(), "i": assessment_id}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> SortKey:
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        created_at = datetime.fromisoformat(payload["c"])
        assessment_id = payload["i"]
    except (binascii.Error, ValueError, KeyError, TypeError) as exc:
        raise InvalidRequestError(f"unrecognised cursor: {exc}") from exc
    if created_at.tzinfo is None or not isinstance(assessment_id, str):
        raise InvalidRequestError("unrecognised cursor: malformed fields")
    return created_at, assessment_id
