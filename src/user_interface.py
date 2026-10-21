"""ввод данных от пользователя"""

from abc import ABC, abstractmethod
from typing import Tuple


class UserInterface(ABC):
    """интерфейс ввода"""

    @abstractmethod
    def get_user_input(self) -> Tuple[str, str, str]:
        """возвращает (логин, пароль, подтверждение)"""
        raise NotImplementedError


class ConsoleUserInterface(UserInterface):
    """ввод с клавиатуры"""

    def get_user_input(self) -> Tuple[str, str, str]:
        login = input("Введите логин: ")
        password = input("Введите пароль: ")
        confirm_password = input("Подтвердите пароль: ")
        return login, password, confirm_password


class ScriptedUserInterface(UserInterface):
    """заглушка: отдаёт заранее заданные ответы"""

    def __init__(self, login: str, password: str, confirm_password: str):
        self._answers = (login, password, confirm_password)

    def get_user_input(self) -> Tuple[str, str, str]:
        return self._answers
