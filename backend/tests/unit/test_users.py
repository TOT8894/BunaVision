import unittest

from app.domain.errors import InvalidRequestError
from app.domain.users import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH, normalize_email, validate_password


class EmailTests(unittest.TestCase):
    def test_is_trimmed_and_lower_cased(self) -> None:
        self.assertEqual(normalize_email("  Worku@Example.COM "), "worku@example.com")

    def test_rejects_malformed_addresses(self) -> None:
        for bad in ("", "no-at-sign", "a@b", "a b@c.com", "@x.com", "x@" + "a" * 260 + ".com"):
            with self.subTest(bad=bad[:20]), self.assertRaises(InvalidRequestError):
                normalize_email(bad)


class PasswordTests(unittest.TestCase):
    def test_accepts_the_allowed_range(self) -> None:
        validate_password("a" * PASSWORD_MIN_LENGTH)
        validate_password("a" * PASSWORD_MAX_LENGTH)

    def test_rejects_too_short_and_too_long(self) -> None:
        for bad in ("a" * (PASSWORD_MIN_LENGTH - 1), "a" * (PASSWORD_MAX_LENGTH + 1)):
            with self.assertRaises(InvalidRequestError):
                validate_password(bad)


if __name__ == "__main__":
    unittest.main()
