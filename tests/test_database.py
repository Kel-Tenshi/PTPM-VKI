import sqlite3
import unittest

from src.database import DatabaseRepository


class TestDatabaseRepository(unittest.TestCase):
    """Тестируем репозиторий SQLite: методы add, get, update, delete и валидацию."""

    def setUp(self) -> None:
        # Поднимаем свежую базу прямо в памяти
        self.repo = DatabaseRepository(":memory:")

    def tearDown(self) -> None:
        # После теста закрываем соединение
        self.repo.close()

    # --- 1. Тесты метода add ---
    def test_add_success(self) -> None:
        """Проверяем добавление записи и совпадение полей."""
        result = self.repo.add(1, "alice", "Привет, мир!")
        self.assertTrue(result)

        record = self.repo.get_by_id(1)
        self.assertIsNotNone(record)
        self.assertEqual(record["id"], 1)
        self.assertEqual(record["name"], "alice")
        self.assertEqual(record["message"], "Привет, мир!")

    def test_add_duplicate_id_raises_integrity_error(self) -> None:
        
        self.repo.add(1, "alice", "Первый пост")
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.add(1, "bob", "Второй такой же пост")

    def test_add_validation_errors(self) -> None:
        # Строка вместо int
        with self.assertRaises(TypeError):
            self.repo.add("не_число", "user", "msg")  # type: ignore

        # Булево значение (True не должно сойти за единицу)
        with self.assertRaises(TypeError):
            self.repo.add(True, "user", "msg")

        # Никнейм длиннее 256 символов
        with self.assertRaises(ValueError):
            self.repo.add(2, "a" * 257, "msg")

        # Пустой никнейм
        with self.assertRaises(ValueError):
            self.repo.add(2, "", "msg")

        # Текст длиннее 8096 символов
        with self.assertRaises(ValueError):
            self.repo.add(2, "user", "m" * 8097)

    # --- 2. Тесты метода get_by_id ---
    def test_get_by_id_existing(self) -> None:
        """Поиск существующей записи по ее ID."""
        self.repo.add(42, "tester", "Ответ на главный вопрос жизни")
        record = self.repo.get_by_id(42)
        self.assertIsInstance(record, dict)
        self.assertEqual(record["name"], "tester")
        self.assertEqual(record["message"], "Ответ на главный вопрос жизни")

    def test_get_by_id_nonexistent_returns_none(self) -> None:
        """Если записи с таким ID нет, метод должен просто вернуть None."""
        record = self.repo.get_by_id(9999)
        self.assertIsNone(record)

    def test_get_by_id_invalid_type(self) -> None:
        """Передача строки вместо числа в ID должна вызывать TypeError."""
        with self.assertRaises(TypeError):
            self.repo.get_by_id("42")  # type: ignore

    # --- 3. Тесты метода get_by_name ---
    def test_get_by_name_returns_all_user_records(self) -> None:
        """Проверяем выборку всех постов нужного автора."""
        self.repo.add(1, "alice", "Пост 1")
        self.repo.add(2, "bob", "Чужой пост")
        self.repo.add(3, "alice", "Пост 2")

        alice_posts = self.repo.get_by_name("alice")
        self.assertEqual(len(alice_posts), 2)
        self.assertEqual([p["id"] for p in alice_posts], [1, 3])

    def test_get_by_name_empty_for_unknown_user(self) -> None:
        """Если у автора нет сообщений, должен вернуться пустой список []."""
        posts = self.repo.get_by_name("unknown_user")
        self.assertEqual(posts, [])

    def test_get_by_name_invalid_type(self) -> None:
        """Передача числа вместо строки в имени автора должна вызывать TypeError."""
        with self.assertRaises(TypeError):
            self.repo.get_by_name(123)  # type: ignore

    # --- 4. Тесты метода update ---
    def test_update_success(self) -> None:
        """Проверяем успешное изменение текста существующего поста."""
        self.repo.add(10, "charlie", "Старый текст")
        result = self.repo.update(10, "Новый исправленный текст")
        self.assertTrue(result)

        updated = self.repo.get_by_id(10)
        self.assertEqual(updated["message"], "Новый исправленный текст")

    def test_update_nonexistent_id_raises_key_error(self) -> None:
        """Попытка обновить несуществующий ID должна кидать KeyError."""
        with self.assertRaises(KeyError):
            self.repo.update(404, "Текст для несуществующего поста")

    def test_update_message_too_long(self) -> None:
        """Нельзя обновить текст на строку длиннее 8096 символов."""
        self.repo.add(11, "charlie", "Короткий текст")
        with self.assertRaises(ValueError):
            self.repo.update(11, "x" * 8097)

    # --- 5. Тесты метода delete ---
    def test_delete_success(self) -> None:
        """Успешное удаление: метод возвращает True, и запись исчезает из базы."""
        self.repo.add(5, "dan", "Пост под удаление")
        deleted = self.repo.delete(5)
        self.assertTrue(deleted)
        self.assertIsNone(self.repo.get_by_id(5))

    def test_delete_nonexistent_id_returns_false(self) -> None:
        """Если удалять нечего, метод должен вернуть False без падения с ошибкой."""
        deleted = self.repo.delete(777)
        self.assertFalse(deleted)

    def test_delete_invalid_type(self) -> None:
        """Передача не-числа в comment_id при удалении должна вызывать TypeError."""
        with self.assertRaises(TypeError):
            self.repo.delete("пять")  # type: ignore


if __name__ == "__main__":
    unittest.main()
