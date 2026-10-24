"""Password hashing with scrypt from the standard library (an OpenSSL KDF).

Stored format: ``scrypt$<n>$<r>$<p>$<salt b64>$<key b64>``. The cost parameters travel with
each hash, so they can be raised later without invalidating existing passwords.

Defaults are one of OWASP's equivalent scrypt settings (N=2^15, r=8, p=3: about 32 MiB and a
fraction of a second per hash). Hashing is CPU-bound, so it runs in a worker thread.
Passwords are encoded as UTF-8 exactly as typed (no normalization).

argon2-cffi is a reasonable alternative if a third-party dependency is acceptable.
"""

import asyncio
import base64
import binascii
import hashlib
import hmac
import secrets

_SCHEME = "scrypt"
_SALT_BYTES = 16
_KEY_BYTES = 32
_DUMMY_PASSWORD = "bunavision-timing-equalizer"


class ScryptPasswordHasher:
    def __init__(self, *, n: int = 2**15, r: int = 8, p: int = 3) -> None:
        self._n, self._r, self._p = n, r, p
        self._dummy_hash = self._hash_sync(_DUMMY_PASSWORD)

    @property
    def dummy_hash(self) -> str:
        return self._dummy_hash

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._hash_sync, password)

    async def verify(self, password: str, password_hash: str) -> bool:
        return await asyncio.to_thread(self._verify_sync, password, password_hash)

    def _hash_sync(self, password: str) -> str:
        salt = secrets.token_bytes(_SALT_BYTES)
        key = _derive(password, salt, self._n, self._r, self._p)
        return "$".join(
            (_SCHEME, str(self._n), str(self._r), str(self._p), _b64(salt), _b64(key))
        )

    @staticmethod
    def _verify_sync(password: str, password_hash: str) -> bool:
        parts = password_hash.split("$")
        if len(parts) != 6 or parts[0] != _SCHEME:
            return False
        try:
            n, r, p = int(parts[1]), int(parts[2]), int(parts[3])
            salt = base64.b64decode(parts[4], validate=True)
            expected = base64.b64decode(parts[5], validate=True)
            actual = _derive(password, salt, n, r, p)
        except (ValueError, binascii.Error):
            return False
        return hmac.compare_digest(actual, expected)


def _derive(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    # OpenSSL refuses to run unless maxmem covers ~128*N*r bytes; allow 2x headroom.
    maxmem = 2 * 128 * n * r + 128 * r * p + 1024 * 1024
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=n, r=r, p=p, maxmem=maxmem, dklen=_KEY_BYTES
    )


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")
