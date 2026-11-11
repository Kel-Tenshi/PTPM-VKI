import sqlite3
from typing import Any, Dict, List, Optional


class DatabaseRepository:
    """Работа с БД SQLite: создание таблицы, сохранение и выборка комментариев."""

    # Лимиты
    MAX_NAME_LENGTH = 256
    MAX_MESSAGE_LENGTH = 8096

    def __init__(self, db_path: str = ":memory:") -> None:
        # По умолчанию база создается в оперативной памяти (удобно для тестов)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        
        # Чтобы получать строки не как кортежи, а как словари по именам колонок
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        """Создаем таблицу comments, если она еще не создана."""
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    message TEXT NOT NULL
                )
                """
            )

    def _validate_comment_id(self, comment_id: Any) -> int:
        
        if not isinstance(comment_id, int) or isinstance(comment_id, bool):
            raise TypeError("ID комментария должен быть целым числом")
        return comment_id

    def _validate_username(self, username: Any) -> str:
        if not isinstance(username, str):
            raise TypeError("Имя пользователя должно быть строкой")
        if not (1 <= len(username) <= self.MAX_NAME_LENGTH):
            raise ValueError(
                f"Длина имени должна быть от 1 до {self.MAX_NAME_LENGTH} символов"
            )
        return username

    def _validate_message(self, message: Any) -> str:
        if not isinstance(message, str):
            raise TypeError("Текст сообщения должен быть строкой")
        if not (0 <= len(message) <= self.MAX_MESSAGE_LENGTH):
            raise ValueError(
                f"Сообщение не должно превышать {self.MAX_MESSAGE_LENGTH} символов"
            )
        return message

    def get_by_id(self, comment_id: int) -> Optional[Dict[str, Any]]:
        """Ищем один комментарий по ID. Если не нашли - возвращаем None."""
        self._validate_comment_id(comment_id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, message FROM comments WHERE id = ?", (comment_id,))
        row = cursor.fetchone()
        return dict(row) if row is not None else None

    def get_by_name(self, username: str) -> List[Dict[str, Any]]:
        """Достаем все комментарии конкретного пользователя."""
        self._validate_username(username)
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, message FROM comments WHERE name = ? ORDER BY id",
            (username,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def add(self, comment_id: int, username: str, message: str) -> bool:
        """Добавляем новый комментарий в базу.

        При дубликате ID сам SQLite выбросит IntegrityError.
        """
        self._validate_comment_id(comment_id)
        self._validate_username(username)
        self._validate_message(message)

        with self.conn:
            self.conn.execute(
                "INSERT INTO comments (id, name, message) VALUES (?, ?, ?)",
                (comment_id, username, message),
            )
        return True

    def update(self, comment_id: int, new_message: str) -> bool:
        """Меняем текст сообщения. Если комментария с таким ID нет - KeyError."""
        self._validate_comment_id(comment_id)
        self._validate_message(new_message)

        with self.conn:
            cursor = self.conn.execute(
                "UPDATE comments SET message = ? WHERE id = ?",
                (new_message, comment_id),
            )
            # Если rowcount == 0, значит запись с таким id не найдена
            if cursor.rowcount == 0:
                raise KeyError(f"Комментарий с ID {comment_id} не найден")
        return True

    def delete(self, comment_id: int) -> bool:
        """Удаляем комментарий по ID. Возвращает True, если удалили, иначе False."""
        self._validate_comment_id(comment_id)
        with self.conn:
            cursor = self.conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
            return cursor.rowcount > 0

    def close(self) -> None:
        """Закрываем соединение с базой."""
        self.conn.close()
