import unittest
from datetime import timedelta

from app.adapters.db.memory_repository import InMemoryUserRepository
from app.adapters.security.passwords import ScryptPasswordHasher
from app.adapters.security.tokens import JwtTokenIssuer
from app.domain.errors import (
    AuthenticationRequiredError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRequestError,
)
from app.domain.users import Role, User
from app.services.auth_service import AuthService
from tests.unit.fakes import CountingIds
from tests.unit.test_security import MutableClock

PASSWORD = "a-long-enough-password"


class AuthTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.clock = MutableClock()
        self.users = InMemoryUserRepository()
        self.hasher = ScryptPasswordHasher(n=2**4, r=8, p=1)
        self.tokens = JwtTokenIssuer(secret="k" * 40, ttl_s=3600, clock=self.clock)
        self.auth = AuthService(
            users=self.users, hasher=self.hasher, tokens=self.tokens,
            clock=self.clock, new_id=CountingIds(),
        )


class RegistrationTests(AuthTestCase):
    async def test_register_creates_a_normal_active_user_with_a_hashed_password(self) -> None:
        user = await self.auth.register(email="  Farmer@Example.com ", password=PASSWORD)
        self.assertEqual(user.email, "farmer@example.com")
        self.assertIs(user.role, Role.USER)
        self.assertTrue(user.is_active)
        self.assertNotIn(PASSWORD, user.password_hash)

    async def test_email_is_unique_regardless_of_case(self) -> None:
        await self.auth.register(email="a@example.com", password=PASSWORD)
        with self.assertRaises(EmailAlreadyRegisteredError):
            await self.auth.register(email="A@EXAMPLE.COM", password=PASSWORD)

    async def test_weak_input_is_rejected_before_anything_is_stored(self) -> None:
        with self.assertRaises(InvalidRequestError):
            await self.auth.register(email="not-an-email", password=PASSWORD)
        with self.assertRaises(InvalidRequestError):
            await self.auth.register(email="b@example.com", password="short")
        self.assertIsNone(await self.users.find_by_email("b@example.com"))

    async def test_only_create_admin_can_make_an_admin(self) -> None:
        normal = await self.auth.register(email="u@example.com", password=PASSWORD)
        admin = await self.auth.create_admin(email="root@example.com", password=PASSWORD)
        self.assertIs(normal.role, Role.USER)
        self.assertIs(admin.role, Role.ADMIN)


class LoginTests(AuthTestCase):
    async def test_login_issues_a_token_for_the_user(self) -> None:
        user = await self.auth.register(email="a@example.com", password=PASSWORD)
        token = await self.auth.login(email="A@example.com", password=PASSWORD)
        self.assertEqual((await self.auth.authenticate(token.access_token)).user_id, user.user_id)

    async def test_every_failure_looks_the_same(self) -> None:
        user = await self.auth.register(email="a@example.com", password=PASSWORD)
        await self.users.add(User(
            user_id="disabled-1", email="off@example.com",
            password_hash=await self.hasher.hash(PASSWORD), role=Role.USER,
            is_active=False, created_at=self.clock.now(),
        ))
        attempts = [
            ("a@example.com", "wrong-password-123"),   # wrong password
            ("nobody@example.com", PASSWORD),           # unknown email
            ("off@example.com", PASSWORD),              # right password, disabled account
        ]
        for email, password in attempts:
            with self.subTest(email=email), self.assertRaises(InvalidCredentialsError) as caught:
                await self.auth.login(email=email, password=password)
            self.assertEqual(caught.exception.public_message, "Incorrect email or password.")
        self.assertTrue(user.is_active)

    async def test_unknown_email_still_spends_a_password_check(self) -> None:
        calls: list[str] = []
        real_verify = self.hasher.verify

        async def spy(password: str, password_hash: str) -> bool:
            calls.append(password_hash)
            return await real_verify(password, password_hash)

        self.hasher.verify = spy  # type: ignore[method-assign]
        with self.assertRaises(InvalidCredentialsError):
            await self.auth.login(email="ghost@example.com", password=PASSWORD)
        self.assertEqual(calls, [self.hasher.dummy_hash])


class AuthenticateTests(AuthTestCase):
    async def test_token_for_a_deleted_or_disabled_user_stops_working(self) -> None:
        user = await self.auth.register(email="a@example.com", password=PASSWORD)
        token = self.tokens.issue(user.user_id).access_token
        self.assertEqual((await self.auth.authenticate(token)).user_id, user.user_id)

        self.users._by_id[user.user_id] = User(
            user_id=user.user_id, email=user.email, password_hash=user.password_hash,
            role=user.role, is_active=False, created_at=user.created_at,
        )
        with self.assertRaises(AuthenticationRequiredError):
            await self.auth.authenticate(token)

    async def test_a_valid_token_for_an_unknown_user_is_rejected(self) -> None:
        token = self.tokens.issue("no-such-user").access_token
        with self.assertRaises(AuthenticationRequiredError):
            await self.auth.authenticate(token)

    async def test_expired_token_is_rejected(self) -> None:
        user = await self.auth.register(email="a@example.com", password=PASSWORD)
        token = self.tokens.issue(user.user_id).access_token
        self.clock.current += timedelta(hours=2)
        with self.assertRaises(AuthenticationRequiredError):
            await self.auth.authenticate(token)


if __name__ == "__main__":
    unittest.main()
