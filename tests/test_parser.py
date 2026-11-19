import os
import re
import unittest
from unittest.mock import MagicMock, patch

from src.database import DatabaseRepository
from src.parser import ForumParser

FIXTURE_NAME = "4pda_thread_673847.html"
FIXTURE_URL = "https://4pda.to/forum/index.php?showtopic=673847"

# Ожидаемые данные зафиксированного слепка живой страницы 4PDA (21 пост).
EXPECTED_IDS = [
    41856548, 41170057, 41171275, 41171319, 41171353, 41171811, 41171949,
    41172375, 41172673, 41173103, 41173116, 41173518, 41173546, 41173556,
    41173569, 41173897, 41173915, 41174023, 41174300, 41174363, 41175339,
]
EXPECTED_NAMES = [
    "Aakurb", "Dimon402", "djdante", "6a/laMyT", "lekars", "utf8", "barsamian",
    "Rufus-Cat", "Panticonur", "Абуш", "Rootdiv", "aleks-man", "Абуш", "Абуш",
    "Абуш", "Юрий З", "Юрий З", "utf8", "Black Fish", "Rootdiv", "utf8",
]


def load_fixture(name: str = FIXTURE_NAME) -> str:
    path = os.path.join(os.path.dirname(__file__), "fixtures", name)
    with open(path, "rb") as f:
        raw = f.read()

    match = re.search(rb"""charset=["']?([\w-]+)""", raw[:4096], re.IGNORECASE)
    encoding = match.group(1).decode("ascii") if match else "utf-8"
    return raw.decode(encoding)


class TestForumParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        # Слепок читаем один раз на весь класс тестов
        cls.sample_html = load_fixture()

    def setUp(self) -> None:
        self.parser = ForumParser()

    def test_parse_html_extracts_all_posts(self) -> None:
        posts = self.parser.parse_html(self.sample_html)
        self.assertEqual(len(posts), len(EXPECTED_IDS))
        self.assertEqual([p["id"] for p in posts], EXPECTED_IDS)

    def test_parse_html_extracts_authors(self) -> None:
        posts = self.parser.parse_html(self.sample_html)
        self.assertEqual([p["name"] for p in posts], EXPECTED_NAMES)
        # Иконка-галочка «ᵥ» из разметки 4PDA не должна попадать в ник
        self.assertNotIn("ᵥ", "".join(p["name"] for p in posts))

    def test_parse_html_preserves_content_markup(self) -> None:
        # Внутренняя HTML-разметка постов должна сохраняться, а не срезаться.
        posts = {p["id"]: p for p in self.parser.parse_html(self.sample_html)}

        # Пост с цитатой другого сообщения
        self.assertIn('<div class="post-block quote">', posts[41172673]["message"])
        # Жирный текст + перенос строки
        self.assertIn("<b>", posts[41173103]["message"])
        self.assertIn("Функционал клиента", posts[41173103]["message"])
        # Спойлер-блок и смайлы-коды остаются как есть
        self.assertIn("<br/>", posts[41171811]["message"])

    def test_parse_html_truncates_long_messages(self) -> None:
        # Ограничение поля message в БД — 8096 символов
        posts = self.parser.parse_html(self.sample_html)
        for post in posts:
            self.assertLessEqual(len(post["message"]), DatabaseRepository.MAX_MESSAGE_LENGTH)

        self.assertEqual(len(posts[0]["message"]), DatabaseRepository.MAX_MESSAGE_LENGTH)

    def test_parse_html_author_fallback_is_anonymous(self) -> None:
        # Если в разметке автора нет совсем — подставляем «Аноним», а не None
        html = '<div data-post="555">Текст без автора</div>'
        posts = self.parser.parse_html(html)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["name"], "Аноним")
        self.assertIn("Текст без автора", posts[0]["message"])

    def test_save_to_db_integration(self) -> None:
        # Проверяем передачу распарсенных данных в базу через репозиторий
        repo = DatabaseRepository(":memory:")
        try:
            posts = self.parser.parse_html(self.sample_html)
            saved_count = self.parser.save_to_db(posts, repo)
            self.assertEqual(saved_count, len(EXPECTED_IDS))

            first = repo.get_by_id(EXPECTED_IDS[0])
            self.assertIsNotNone(first)
            self.assertEqual(first["name"], EXPECTED_NAMES[0])

            abush_posts = repo.get_by_name("Абуш")
            self.assertEqual([p["id"] for p in abush_posts], [41173103, 41173546, 41173556, 41173569])

            # Повторный разбор той же страницы не падает и не плодит дубли
            re_saved = self.parser.save_to_db(posts, repo, ignore_duplicates=True)
            self.assertEqual(re_saved, 0)
        finally:
            repo.close()

    @patch("requests.Session.get")
    def test_parse_page_with_mocked_network(self, mock_get: MagicMock) -> None:
        # Скачивание страницы: подстановка User-Agent и вызов get без реальной сети.
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        posts = self.parser.parse_page(FIXTURE_URL)

        mock_get.assert_called_once_with(FIXTURE_URL, timeout=15)
        mock_response.raise_for_status.assert_called_once()
        self.assertEqual(len(posts), len(EXPECTED_IDS))

        # Проверяем, что в заголовках действительно прописан браузерный User-Agent
        self.assertIn("User-Agent", self.parser.session.headers)
        self.assertIn("Mozilla/5.0", self.parser.session.headers["User-Agent"])


if __name__ == "__main__":
    unittest.main()
