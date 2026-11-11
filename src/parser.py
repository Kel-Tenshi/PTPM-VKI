import re
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup

from .database import DatabaseRepository


class ForumParser:
    """Парсер страниц форума (4PDA)."""

    # User-Agent, чтобы сайт не блокировал запросы с 403
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        self.session = session or requests.Session()
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.session.headers.update({"User-Agent": self.user_agent})

    def parse_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Разбираем готовый HTML и вытаскиваем посты: id, автора и текст сообщения."""
        soup = BeautifulSoup(html_content, "html.parser")
        comments: List[Dict[str, Any]] = []

        # На 4PDA посты обычно лежат в блоках с data-post, id="entryXXXX" или классом post_container
        post_elements = soup.select("[data-post], div[id^='entry'], table[id^='entry'], .post_container")

        # Запасной вариант, если на странице просто блоки с текстом постов
        if not post_elements:
            post_elements = soup.find_all(attrs={"class": re.compile(r"post_body|postcolor")})

        # Защита от дублей, если селекторы захватили родительский и дочерний контейнеры
        seen_ids = set()

        for el in post_elements:
            # 1. Извлекаем ID поста
            comment_id = None
            if el.has_attr("data-post"):
                raw_id = el["data-post"]
                if raw_id.isdigit():
                    comment_id = int(raw_id)
            elif el.has_attr("id") and el["id"].startswith("entry"):
                digits = re.findall(r"\d+", el["id"])
                if digits:
                    comment_id = int(digits[0])

            # Если в самом блоке ID нет, ищем внутреннюю ссылку/якорь на пост
            if comment_id is None:
                anchor = el.find(attrs={"name": re.compile(r"^entry\d+$")}) or el.find(
                    "a", href=re.compile(r"#entry\d+")
                )
                if anchor:
                    val = anchor.get("name") or anchor.get("href", "")
                    digits = re.findall(r"\d+", val)
                    if digits:
                        comment_id = int(digits[0])

            if comment_id is None or comment_id in seen_ids:
                continue

            # 2. Извлекаем никнейм автора
            name = None
            name_el = (
                el.select_one(".normalname a, .normalname, .nickname, [data-author], .post-author a")
            )
            if name_el:
                name = name_el.get_text(strip=True)
            elif el.has_attr("data-author"):
                name = el["data-author"].strip()

            if not name:
                name = "Аноним"
            # Обрезаем под лимит колонки в БД, если ник слишком длинный
            name = name[: DatabaseRepository.MAX_NAME_LENGTH]

            # 3. Извлекаем тело сообщения с сохранением тегов (жирный шрифт, курсив, ссылки)
            body_el = el.select_one(".post_body, .postcolor, .post-content, .entry-content")
            if body_el is None:
                if any("post_body" in cls or "postcolor" in cls for cls in el.get("class", [])):
                    body_el = el
                else:
                    body_el = el

            # Сохраняем разметку внутри сообщения
            message = "".join(str(child) for child in body_el.contents).strip()
            if not message:
                message = body_el.get_text(strip=True)

            message = message[: DatabaseRepository.MAX_MESSAGE_LENGTH]

            seen_ids.add(comment_id)
            comments.append(
                {
                    "id": comment_id,
                    "name": name,
                    "message": message,
                }
            )

        return comments

    def parse_page(self, url: str) -> List[Dict[str, Any]]:
        """Качаем страницу по ссылке и передаем ее в parse_html."""
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        return self.parse_html(response.text)

    def save_to_db(
        self,
        parsed_data: List[Dict[str, Any]],
        repository: DatabaseRepository,
        ignore_duplicates: bool = True,
    ) -> int:
        """Сохраняем распарсенные посты в базу через DatabaseRepository.

        Если ignore_duplicates=True, посты с уже существующими ID пропускаем.
        """
        saved_count = 0
        for item in parsed_data:
            try:
                repository.add(
                    comment_id=item["id"],
                    username=item["name"],
                    message=item["message"],
                )
                saved_count += 1
            except Exception:
                # Если отключили пропуск дублей — пробрасываем ошибку дальше
                if not ignore_duplicates:
                    raise
        return saved_count
