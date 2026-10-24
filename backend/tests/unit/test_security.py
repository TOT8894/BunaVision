import unittest
from datetime import UTC, datetime, timedelta

import jwt

from app.adapters.security.passwords import ScryptPasswordHasher
from app.adapters.security.tokens import ISSUER, JwtTokenIssuer
from app.domain.errors import AuthenticationRequiredError

SECRET = "s" * 40


class MutableClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 10, 23, 9, 0, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current

    def monotonic(self) -> float:
        return 0.0


class PasswordHasherTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.hasher = ScryptPasswordHasher(n=2**4, r=8, p=1)  # cheap for tests only

    async def test_round_trip_and_wrong_password(self) -> None:
        hashed = await self.hasher.hash("correct horse battery")
        self.assertTrue(await self.hasher.verify("correct horse battery", hashed))
        self.assertFalse(await self.hasher.verify("correct horse batterz", hashed))

    async def test_same_password_gets_a_different_salt_each_time(self) -> None:
        self.assertNotEqual(await self.hasher.hash("same-password-1"), await self.hasher.hash("same-password-1"))

    async def test_hash_records_its_own_cost_parameters(self) -> None:
        hashed = await self.hasher.hash("whatever-password")
        self.assertTrue(hashed.startswith("scrypt$16$8$1$"))
        stronger = ScryptPasswordHasher(n=2**5, r=8, p=1)
        self.assertTrue(await stronger.verify("whatever-password", hashed))  # old hashes still verify

    async def test_malformed_hashes_never_verify(self) -> None:
        for bad in ("", "plaintext", "scrypt$x$8$1$abc$def", "scrypt$16$8$1$!!$!!", "md5$1$2$3$4$5"):
            with self.subTest(bad=bad):
                self.assertFalse(await self.hasher.verify("anything-at-all", bad))

    async def test_dummy_hash_is_a_valid_hash_nobody_knows_the_password_of(self) -> None:
        self.assertTrue(self.hasher.dummy_hash.startswith("scrypt$"))
        self.assertFalse(await self.hasher.verify("guess-1234567", self.hasher.dummy_hash))


class TokenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = MutableClock()
        self.tokens = JwtTokenIssuer(secret=SECRET, ttl_s=3600, clock=self.clock)

    def test_round_trip(self) -> None:
        issued = self.tokens.issue("user-1")
        self.assertEqual(issued.expires_in_s, 3600)
        self.assertEqual(self.tokens.subject_of(issued.access_token), "user-1")

    def test_expires_by_our_clock(self) -> None:
        token = self.tokens.issue("user-1").access_token
        self.clock.current += timedelta(seconds=3599)
        self.assertEqual(self.tokens.subject_of(token), "user-1")
        self.clock.current += timedelta(seconds=1)
        with self.assertRaises(AuthenticationRequiredError):
            self.tokens.subject_of(token)

    def test_rejects_garbage_and_wrong_signature(self) -> None:
        other = JwtTokenIssuer(secret="x" * 40, ttl_s=3600, clock=self.clock)
        for bad in ("", "not.a.jwt", other.issue("user-1").access_token):
            with self.subTest(bad=bad[:12]), self.assertRaises(AuthenticationRequiredError):
                self.tokens.subject_of(bad)

    def test_rejects_the_none_algorithm(self) -> None:
        payload = {"iss": ISSUER, "sub": "user-1", "iat": 0, "exp": 9_999_999_999}
        unsigned = jwt.encode(payload, key=None, algorithm="none")
        with self.assertRaises(AuthenticationRequiredError):
            self.tokens.subject_of(unsigned)

    def test_rejects_tokens_from_another_issuer_or_missing_claims(self) -> None:
        now = int(self.clock.now().timestamp())
        wrong_issuer = jwt.encode({"iss": "someone-else", "sub": "u", "iat": now, "exp": now + 60}, SECRET, algorithm="HS256")
        no_subject = jwt.encode({"iss": ISSUER, "iat": now, "exp": now + 60}, SECRET, algorithm="HS256")
        for bad in (wrong_issuer, no_subject):
            with self.assertRaises(AuthenticationRequiredError):
                self.tokens.subject_of(bad)


if __name__ == "__main__":
    unittest.main()
