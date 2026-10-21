"""работа с базой sqlite"""

import os
import sqlite3
from typing import Optional, Tuple


class DatabaseHandler:
    """хранит результаты проверки регистрации

    соединение с базой одно на весь объект: каждое отдельное подключение
    к ":memory:" - это отдельная пустая база, и таблица из одного не видна
    в другом
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path

        # папку под файл базы создаём сами, иначе FileNotFoundError
        if db_path != ":memory:":
            folder = os.path.dirname(os.path.abspath(db_path))
            if folder:
                os.makedirs(folder, exist_ok=True)

        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._init_db()

    # -внутреннее-

    def _init_db(self) -> None:
        """создаёт таблицу, если её ещё нет"""
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS registration_logs (
                    login TEXT NOT NULL,
                    password TEXT NOT NULL,
                    confirm_password TEXT NOT NULL,
                    result INTEGER NOT NULL,
                    error_message TEXT NOT NULL,
                    PRIMARY KEY (login, password, confirm_password)
                )
                """
            )

    # -запись, чтение, удаление-

    def add_record(
        self,
        login: str,
        password: str,
        confirm_password: str,
        result: bool,
        error_message: str,
    ) -> None:
        """добавляет запись, по тому же ключу перезаписывает"""
        with self._connection:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO registration_logs
                    (login, password, confirm_password, result, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (login, password, confirm_password, 1 if result else 0, error_message or ""),
            )

    def get_record(
        self, login: str, password: str, confirm_password: str
    ) -> Optional[Tuple[bool, str]]:
        """возвращает (результат, текст ошибки) или None, если записи нет"""
        cursor = self._connection.execute(
            """
            SELECT result, error_message FROM registration_logs
            WHERE login = ? AND password = ? AND confirm_password = ?
            """,
            (login, password, confirm_password),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return bool(row["result"]), row["error_message"]

    def delete_record(self, login: str, password: str, confirm_password: str) -> bool:
        """удаляет запись, True - если она была"""
        with self._connection:
            cursor = self._connection.execute(
                """
                DELETE FROM registration_logs
                WHERE login = ? AND password = ? AND confirm_password = ?
                """,
                (login, password, confirm_password),
            )
        return cursor.rowcount > 0

    # -служебное-

    def count_records(self) -> int:
        """сколько всего записей"""
        cursor = self._connection.execute("SELECT COUNT(*) FROM registration_logs")
        return int(cursor.fetchone()[0])

    def close(self) -> None:
        """закрывает соединение"""
        self._connection.close()
