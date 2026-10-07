import unittest
from src.validator import mask_password, validate_registration


class TestRegistrationValidation(unittest.TestCase):

    # ==========================================
    # 1. Позитивные сценарии (успешная регистрация)
    # ==========================================

    def test_successful_registration_with_phone_number(self):
        status, msg = validate_registration("+7-999-123-4567", "Пароль123!", "Пароль123!")
        self.assertTrue(status)
        self.assertEqual(msg, "")

    def test_successful_registration_with_email_address(self):
        status, msg = validate_registration("student@edu.university.ru", "Секрет_2026#", "Секрет_2026#")
        self.assertTrue(status)
        self.assertEqual(msg, "")

    def test_successful_registration_with_valid_string_login(self):
        status, msg = validate_registration("ivan_petrov_99", "МойКод99?", "МойКод99?")
        self.assertTrue(status)
        self.assertEqual(msg, "")

    def test_successful_registration_with_minimum_valid_password_length(self):
        # Граничное значение: ровно 7 символов
        status, msg = validate_registration("valid_user", "Абв12!?", "Абв12!?")
        self.assertTrue(status)
        self.assertEqual(msg, "")

    # ==========================================
    # 2. Негативные сценарии: Проверка логина
    # ==========================================

    def test_registration_fails_when_login_is_empty_string(self):
        status, msg = validate_registration("", "Пароль123!", "Пароль123!")
        self.assertFalse(status)
        self.assertIn("не может быть пустым", msg)

    def test_registration_fails_when_login_contains_only_whitespace(self):
        status, msg = validate_registration("   ", "Пароль123!", "Пароль123!")
        self.assertFalse(status)
        self.assertIn("не может быть пустым", msg)

    def test_registration_fails_when_login_is_blacklisted(self):
        status, msg = validate_registration("admin", "Пароль123!", "Пароль123!")
        self.assertFalse(status)
        self.assertIn("черном списке", msg)

    def test_registration_fails_when_login_is_blacklisted_uppercase(self):
        status, msg = validate_registration("ROOT", "Пароль123!", "Пароль123!")
        self.assertFalse(status)
        self.assertIn("черном списке", msg)

    def test_registration_fails_when_string_login_is_shorter_than_five_chars(self):
        status, msg = validate_registration("usr", "Пароль123!", "Пароль123!")
        self.assertFalse(status)
        self.assertIn("слишком короткий", msg)

    def test_registration_fails_when_string_login_has_forbidden_characters(self):
        status, msg = validate_registration("user-name!", "Пароль123!", "Пароль123!")
        self.assertFalse(status)
        self.assertIn("недопустимые символы", msg)

    def test_registration_fails_when_phone_number_format_is_incorrect(self):
        status, msg = validate_registration("+7-999-00", "Пароль123!", "Пароль123!")
        self.assertFalse(status)
        self.assertIn("не соответствует формату", msg)

    def test_registration_fails_when_email_lacks_at_symbol(self):
        status, msg = validate_registration("usermail.ru", "Пароль123!", "Пароль123!")
        self.assertFalse(status)
        self.assertIn("недопустимые символы", msg)

    def test_registration_fails_when_login_is_not_string_type(self):
        status, msg = validate_registration(89991234567, "Пароль123!", "Пароль123!")
        self.assertFalse(status)
        self.assertIn("должен быть строкой", msg)

    # ==========================================
    # 3. Негативные сценарии: Проверка пароля
    # ==========================================

    def test_registration_fails_when_password_is_empty(self):
        status, msg = validate_registration("valid_login", "", "")
        self.assertFalse(status)
        self.assertIn("не может быть пустым", msg)

    def test_registration_fails_when_passwords_do_not_match(self):
        status, msg = validate_registration("valid_login", "Пароль123!", "Пароль999!")
        self.assertFalse(status)
        self.assertIn("не совпадают", msg)

    def test_registration_fails_when_password_is_shorter_than_seven_chars(self):
        status, msg = validate_registration("valid_login", "Пас1!", "Пас1!")
        self.assertFalse(status)
        self.assertIn("слишком короткий", msg)

    def test_registration_fails_when_password_contains_latin_alphabet(self):
        status, msg = validate_registration("valid_login", "Password123!", "Password123!")
        self.assertFalse(status)
        self.assertIn("латиница запрещена", msg)

    def test_registration_fails_when_password_lacks_uppercase_cyrillic(self):
        status, msg = validate_registration("valid_login", "пароль123!", "пароль123!")
        self.assertFalse(status)
        self.assertIn("заглавную букву", msg)

    def test_registration_fails_when_password_lacks_lowercase_cyrillic(self):
        status, msg = validate_registration("valid_login", "ПАРОЛЬ123!", "ПАРОЛЬ123!")
        self.assertFalse(status)
        self.assertIn("строчную букву", msg)

    def test_registration_fails_when_password_lacks_digits(self):
        status, msg = validate_registration("valid_login", "ПарольСпец!", "ПарольСпец!")
        self.assertFalse(status)
        self.assertIn("минимум одну цифру", msg)

    def test_registration_fails_when_password_lacks_special_characters(self):
        status, msg = validate_registration("valid_login", "Пароль12345", "Пароль12345")
        self.assertFalse(status)
        self.assertIn("специальный символ", msg)

    def test_registration_fails_when_password_is_not_string_type(self):
        status, msg = validate_registration("valid_login", 12345678, 12345678)
        self.assertFalse(status)
        self.assertIn("должны быть строками", msg)

    # ==========================================
    # 4. Проверка функции маскирования
    # ==========================================

    def test_mask_password_handles_empty_string_input(self):
        self.assertEqual(mask_password(""), "<empty>")

    def test_mask_password_handles_none_object(self):
        self.assertEqual(mask_password(None), "<None>")


if __name__ == "__main__":
    unittest.main()