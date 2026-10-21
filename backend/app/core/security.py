"""Identity of the caller.

AUTH IS NOT IMPLEMENTED  YET. Until it is, `get_principal` in `app.api.dependencies` returns one
shared demo principal, so every caller sees every record. The rest of the code is already
owner-scoped: every repository call takes an `owner_id`. Choosing an auth mechanism therefore
changes that one dependency and nothing else.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: str
