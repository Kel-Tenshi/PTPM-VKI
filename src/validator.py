"""правила регистрации (из ЛР1/ЛР2)"""

import hashlib
import re
from typing import Tuple

BLACKLIST = {"admin", "root", "superuser", "moderator", "support", "test", "owner"}
PHONE_PATTERN = re.compile(r"^\+\d-\d{3}-\d{3}-\d{4}$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
STRING_LOGIN_PATTERN = re.compile(r"^[a-zA-Z0-9_]{5,}$")
SPECIAL_CHARS = set("!@#$%^&*()_-+=[]{}|;:,.<>?/~`'\"\\")
ALLOWED_PASSWORD_CHARS = (
    set("абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ0123456789")
    | SPECIAL_CHARS
)


def mask_password(pwd: str) -> str:
    """маскирует пароль, чтобы в лог не утекло само значение"""
    if pwd is None:
        return "<None>"
    if pwd == "":
        return "<empty>"
    hashed = hashlib.sha256(("salt_for_mask_" + str(pwd)).encode("utf-8")).hexdigest()[:8]
    return f"***MASKED_{hashed}***"


def validate_registration(login: str, password: str, confirm_password: str) -> Tuple[bool, str]:
    """возвращает (ок/не ок, текст ошибки)"""
    if not isinstance(login, str):
        return False, "Логин должен быть строкой"
    if not isinstance(password, str) or not isinstance(confirm_password, str):
        return False, "Пароль и подтверждение должны быть строками"

    if not login or not login.strip():
        return False, "Логин не может быть пустым"

    login = login.strip()

    if login.lower() in BLACKLIST:
        return False, "Логин находится в черном списке запрещенных имен"

    is_phone = bool(PHONE_PATTERN.match(login))
    is_email = bool(EMAIL_PATTERN.match(login))
    is_valid_str = bool(STRING_LOGIN_PATTERN.match(login))

    if not (is_phone or is_email or is_valid_str):
        if "@" not in login and not login.startswith("+"):
            if len(login) < 5:
                return False, "Строковый логин слишком короткий (минимальная длина 5 символов)"
            if not re.match(r"^[a-zA-Z0-9_]+$", login):
                return False, "Строковый логин содержит недопустимые символы (разрешены только латиница, цифры и _)"
        return False, "Логин не соответствует формату (телефон +x-xxx-xxx-xxxx, email или строка [a-zA-Z0-9_]>=5)"

    if not password:
        return False, "Пароль не может быть пустым"
    if password != confirm_password:
        return False, "Пароль и подтверждение пароля не совпадают"
    if len(password) < 7:
        return False, "Пароль слишком короткий (минимальная длина 7 символов)"
    if any(char not in ALLOWED_PASSWORD_CHARS for char in password):
        return False, "Пароль содержит недопустимые символы (латиница запрещена, разрешена только кириллица, цифры и спецсимволы)"
    if not re.search(r"[А-ЯЁ]", password):
        return False, "Пароль должен содержать минимум одну заглавную букву (кириллица)"
    if not re.search(r"[а-яё]", password):
        return False, "Пароль должен содержать минимум одну строчную букву (кириллица)"
    if not re.search(r"\d", password):
        return False, "Пароль должен содержать минимум одну цифру"
    if not any(char in SPECIAL_CHARS for char in password):
        return False, "Пароль должен содержать минимум один специальный символ"

    return True, ""


class RegistrationValidator:
    """класс вычислений из ЛР1"""

    def validate(self, login: str, password: str, confirm_password: str) -> Tuple[bool, str]:
        return validate_registration(login, password, confirm_password)
