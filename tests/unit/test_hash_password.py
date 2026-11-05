import unittest
from src.core.security.argon_hasher import password_hash, verify_password


class TestHashPassword(unittest.TestCase):

    def test_hash_returns_string(self):
        """Хэшированный пароль должен быть строкой"""
        password = "test_password_123"
        hashed = password_hash(password)

        self.assertIsInstance(hashed, str)
        self.assertGreaterEqual(len(hashed), 0)

    def test_different_hashes_for_same_password(self):
        """
        Один и тот же пароль должен давать разные хэши
        Это обычно происходит из-за добавления случайной соли
        """
        password = "repeated_password"
        hash1 = password_hash(password)
        hash2 = password_hash(password)

        self.assertIsNot(hash1, hash2)

    def test_verify_correct_password(self):
        """Верификация должна возвращать True для неправильного пароля"""

        password = "secure_password"
        hashed = password_hash(password)
        verify = verify_password(password, hashed)

        self.assertTrue(hashed, verify)

    def test_verify_incorrect_password(self):
        """Верификация должна возвращать False"""

        password = "correct_password"
        wrong_password = "wrong_password"

        hashed = password_hash(password)
        verify = verify_password(wrong_password, hashed)

        self.assertFalse(verify)
