import hashlib
import re
from typing import Tuple

BLACKLIST = {"admin", "root", "superuser", "moderator", "support", "test", "owner"}

PHONE_PATTERN = re.compile(r"^\+\d-\d{3}-\d{3}-\d{4}$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
STRING_LOGIN_PATTERN = re.compile(r"^[a-zA-Z0-9_]{5,}$")

SPECIAL_CHARS = set("!@#$%^&*()_-+=[]{}|;:,.<>?/~`'\"\\")

ALLOWED_PASSWORD_CHARS = (
    set(
        "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        "0123456789"
    )
    | SPECIAL_CHARS
)


def mask_password(pwd) -> str:
    """
    Маскирует пароль для логов.
    """
    if pwd is None:
        return "<None>"
    if pwd == "":
        return "<empty>"

    hashed = hashlib.sha256(("salt_for_mask_" + str(pwd)).encode("utf-8")).hexdigest()[:8]
    return f"***MASKED_{hashed}***"


def validate_registration(
    login: str, password: str, confirm_password: str
) -> Tuple[bool, str]:
    """
    Проверяет учетные данные пользователя.
    Возвращает (True, "") при успехе или (False, "причина") при ошибке.
    """
    # 1. Логин: наличие
    if not login or not login.strip():
        return False, "Логин не может быть пустым"

    login = login.strip()

    # 2. Логин: черный список
    if login.lower() in BLACKLIST:
        return False, "Логин находится в черном списке запрещенных имен"

    # 3. Логин: формат (телефон, email или строка)
    is_phone = bool(PHONE_PATTERN.match(login))
    is_email = bool(EMAIL_PATTERN.match(login))
    is_valid_str = bool(STRING_LOGIN_PATTERN.match(login))

    if not (is_phone or is_email or is_valid_str):
        # уточняем причину для строкового логина
        if "@" not in login and not login.startswith("+"):
            if len(login) < 5:
                return (
                    False,
                    "Строковый логин слишком короткий (минимальная длина 5 символов)",
                )
            if not re.match(r"^[a-zA-Z0-9_]+$", login):
                return (
                    False,
                    "Строковый логин содержит недопустимые символы "
                    "(разрешены только латиница, цифры и _)",
                )
        return (
            False,
            "Логин не соответствует формату "
            "(телефон +x-xxx-xxx-xxxx, email или строка [a-zA-Z0-9_]>=5)",
        )

    # 4. Пароль: наличие
    if not password:
        return False, "Пароль не может быть пустым"

    # 5. Пароль: совпадение с подтверждением
    if password != confirm_password:
        return False, "Пароль и подтверждение пароля не совпадают"

    # 6. Пароль: длина
    if len(password) < 7:
        return False, "Пароль слишком короткий (минимальная длина 7 символов)"

    # 7. Пароль: только кириллица, цифры и спецсимволы
    if any(char not in ALLOWED_PASSWORD_CHARS for char in password):
        return (
            False,
            "Пароль содержит недопустимые символы "
            "(латиница запрещена, разрешена только кириллица, цифры и спецсимволы)",
        )

    # 8. Пароль: заглавная буква
    if not re.search(r"[А-ЯЁ]", password):
        return False, "Пароль должен содержать минимум одну заглавную букву (кириллица)"

    # 9. Пароль: строчная буква
    if not re.search(r"[а-яё]", password):
        return False, "Пароль должен содержать минимум одну строчную букву (кириллица)"

    # 10. Пароль: цифра
    if not re.search(r"\d", password):
        return False, "Пароль должен содержать минимум одну цифру"

    # 11. Пароль: спецсимвол
    if not any(char in SPECIAL_CHARS for char in password):
        return False, "Пароль должен содержать минимум один специальный символ"

    return True, ""