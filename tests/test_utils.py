import unittest
from contacts.utils import hash_password, verify_password, verify_access_token
from unittest.mock import patch

class TestUtils(unittest.TestCase):
    def test_hash_password(self):
        password = "testpassword"
        hashed_password = hash_password(password)
        self.assertNotEqual(hashed_password, password)  # Хешированный пароль должен быть другим
        self.assertTrue(verify_password(password, hashed_password))  # Проверка пароля

    def test_verify_password_invalid(self):
        password = "testpassword"
        hashed_password = hash_password(password)
        self.assertFalse(verify_password("wrongpassword", hashed_password))  # Ошибка при неверном пароле

    @patch("contacts.utils.jwt.decode")
    def test_verify_access_token_valid(self, mock_decode):
        # Мокаем decode для теста
        mock_decode.return_value = {"sub": 1}
        token = "valid_token"
        result = verify_access_token(token)
        self.assertEqual(result["sub"], 1)

    @patch('contacts.utils.jwt.decode')
    def test_verify_access_token_invalid(self, mock_decode):
        # Мокаем неверный токен
        mock_decode.side_effect = Exception("Invalid token")
        with self.assertRaises(Exception):
            verify_access_token("invalid_token")

if __name__ == '__main__':
    unittest.main()
