import os
import unittest
from unittest.mock import MagicMock, patch

from src.database import DatabaseRepository
from src.parser import ForumParser


class TestForumParser(unittest.TestCase):
    """Тестируем парсер форума: разбор HTML-слепка, сохранение тегов и запись в БД."""

    @classmethod
    def setUpClass(cls) -> None:
        # Читаем локальный HTML-слепок, чтобы тесты не дергали реальную сеть
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_forum.html"
        )
        with open(fixture_path, "r", encoding="utf-8") as f:
            cls.sample_html = f.read()

    def setUp(self) -> None:
        self.parser = ForumParser()

    def test_parse_html_extracts_all_posts(self) -> None:
        """Парсер должен найти все 3 поста со слепка, их ID и ники авторов."""
        posts = self.parser.parse_html(self.sample_html)
        self.assertEqual(len(posts), 3)

        ids = [p["id"] for p in posts]
        self.assertEqual(ids, [10101, 10102, 10103])

        names = [p["name"] for p in posts]
        self.assertEqual(names, ["Alice_Dev", "Bob_Tester", "Charlie_4PDA"])

    def test_parse_html_preserves_content_markup(self) -> None:
        """Проверяем, что внутренняя HTML-разметка постов не теряется."""
        posts = self.parser.parse_html(self.sample_html)

        # Жирный текст в первом посте
        self.assertIn("<b>первое сообщение</b>", posts[0]["message"])
        # Курсив во втором посте
        self.assertIn("<i>дополнительная</i>", posts[1]["message"])
        # Ссылка в третьем посте
        self.assertIn('<a href="https://4pda.to">Перейти</a>', posts[2]["message"])

    def test_save_to_db_integration(self) -> None:
        """Проверяем передачу распарсенных данных в базу данных через репозиторий."""
        repo = DatabaseRepository(":memory:")
        try:
            posts = self.parser.parse_html(self.sample_html)
            saved_count = self.parser.save_to_db(posts, repo)
            self.assertEqual(saved_count, 3)

            # Проверяем, что посты реально записались в БД и читаются
            first = repo.get_by_id(10101)
            self.assertIsNotNone(first)
            self.assertEqual(first["name"], "Alice_Dev")

            second = repo.get_by_id(10102)
            self.assertIsNotNone(second)
            self.assertEqual(second["name"], "Bob_Tester")

            third = repo.get_by_id(10103)
            self.assertIsNotNone(third)
            self.assertEqual(third["name"], "Charlie_4PDA")

            # Повторный запуск с ignore_duplicates=True не должен падать и возвращает 0 новых записей
            re_saved = self.parser.save_to_db(posts, repo, ignore_duplicates=True)
            self.assertEqual(re_saved, 0)
        finally:
            repo.close()

    @patch("requests.Session.get")
    def test_parse_page_with_mocked_network(self, mock_get: MagicMock) -> None:
        """Проверяем скачивание страницы: подстановку User-Agent и вызов get без реальной сети."""
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        posts = self.parser.parse_page("https://4pda.to/forum/index.php?showtopic=12345")

        mock_get.assert_called_once_with(
            "https://4pda.to/forum/index.php?showtopic=12345", timeout=15
        )
        mock_response.raise_for_status.assert_called_once()
        self.assertEqual(len(posts), 3)

        # Проверяем, что в заголовках действительно прописан браузерный User-Agent
        self.assertIn("User-Agent", self.parser.session.headers)
        self.assertIn("Mozilla/5.0", self.parser.session.headers["User-Agent"])


if __name__ == "__main__":
    unittest.main()
