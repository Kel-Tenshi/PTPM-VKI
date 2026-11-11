"""Интерактивная консольная утилита для работы с парсером и базой данных."""

import os
import sys
from typing import Any, Dict, List

from src.database import DatabaseRepository
from src.parser import ForumParser

DEFAULT_DB_FILE = "forum_data.db"


def print_comment(comment: Dict[str, Any]) -> None:
    """Аккуратно выводим комментарий в консоль."""
    print(f"[{comment['id']}] Автор: {comment['name']}")
    print(f"Текст:\n{comment['message']}\n" + "-" * 40)


def print_comments_table(comments: List[Dict[str, Any]]) -> None:
    """Вывод списка комментариев."""
    if not comments:
        print("Записей не найдено.")
        return

    print(f"\nНайдено записей: {len(comments)}")
    print("-" * 60)
    for c in comments:
        # Для общего списка подрезаем слишком длинные посты
        short_msg = c["message"] if len(c["message"]) <= 100 else c["message"][:97] + "..."
        # Убираем переводы строк для компактности
        short_msg = short_msg.replace("\n", " ")
        print(f"ID: {c['id']:<8} | Автор: {c['name']:<18} | {short_msg}")
    print("-" * 60)


def parse_url_menu(parser: ForumParser, repo: DatabaseRepository) -> None:
    """Скачивание по URL и сохранение в БД."""
    url = input("Введите URL темы на форуме (например, 4PDA): ").strip()
    if not url:
        print("URL не может быть пустым.")
        return

    print("Скачиваем и парсим страницу...")
    try:
        posts = parser.parse_page(url)
        print(f"Найдено постов на странице: {len(posts)}")
        if posts:
            saved = parser.save_to_db(posts, repo, ignore_duplicates=True)
            print(f"Успешно сохранено новых постов в базу: {saved}")
    except Exception as e:
        print(f"Ошибка при парсинге URL: {e}")


def parse_file_menu(parser: ForumParser, repo: DatabaseRepository) -> None:
    """Загрузка постов из локального HTML-файла."""
    file_path = input("Введите путь к HTML-файлу (Enter для 'tests/fixtures/sample_forum.html'): ").strip()
    if not file_path:
        file_path = os.path.join("tests", "fixtures", "sample_forum.html")

    if not os.path.isfile(file_path):
        print(f"Файл не найден: {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        posts = parser.parse_html(html_content)
        print(f"Найдено постов в файле: {len(posts)}")
        if posts:
            saved = parser.save_to_db(posts, repo, ignore_duplicates=True)
            print(f"Успешно сохранено новых постов в базу: {saved}")
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")


def get_by_id_menu(repo: DatabaseRepository) -> None:
    """Поиск по ID."""
    raw_id = input("Введите ID комментария: ").strip()
    if not raw_id.isdigit():
        print("ID должен быть числом.")
        return

    comment = repo.get_by_id(int(raw_id))
    if comment:
        print("\nНайден комментарий:")
        print_comment(comment)
    else:
        print(f"Комментарий с ID {raw_id} не найден.")


def get_by_name_menu(repo: DatabaseRepository) -> None:
    """Поиск по никнейму автора."""
    name = input("Введите никнейм автора: ").strip()
    if not name:
        print("Никнейм не может быть пустым.")
        return

    comments = repo.get_by_name(name)
    print_comments_table(comments)


def add_comment_menu(repo: DatabaseRepository) -> None:
    """Ручное добавление комментария."""
    raw_id = input("Введите уникальный ID: ").strip()
    if not raw_id.isdigit():
        print("ID должен быть числом.")
        return

    name = input("Введите имя автора (до 256 символов): ").strip()
    print("Введите текст сообщения (до 8096 символов). Для завершения нажмите Enter:")
    message = input("> ").strip()

    try:
        repo.add(int(raw_id), name, message)
        print("Комментарий успешно добавлен в базу.")
    except Exception as e:
        print(f"Не удалось добавить комментарий: {e}")


def update_comment_menu(repo: DatabaseRepository) -> None:
    """Обновление текста существующего комментария."""
    raw_id = input("Введите ID комментария для изменения: ").strip()
    if not raw_id.isdigit():
        print("ID должен быть числом.")
        return

    comment_id = int(raw_id)
    existing = repo.get_by_id(comment_id)
    if not existing:
        print(f"Комментарий с ID {comment_id} не существует.")
        return

    print(f"Текущий текст:\n{existing['message']}")
    new_message = input("Введите новый текст: ").strip()

    try:
        repo.update(comment_id, new_message)
        print("Текст комментария обновлен.")
    except Exception as e:
        print(f"Ошибка при обновлении: {e}")


def delete_comment_menu(repo: DatabaseRepository) -> None:
    """Удаление комментария по ID."""
    raw_id = input("Введите ID для удаления: ").strip()
    if not raw_id.isdigit():
        print("ID должен быть числом.")
        return

    comment_id = int(raw_id)
    if repo.delete(comment_id):
        print(f"Комментарий с ID {comment_id} удален.")
    else:
        print(f"Комментарий с ID {comment_id} не найден.")


def show_all_comments_menu(repo: DatabaseRepository) -> None:
    """Вывод всех комментариев из базы."""
    cursor = repo.conn.cursor()
    cursor.execute("SELECT id, name, message FROM comments ORDER BY id")
    rows = [dict(r) for r in cursor.fetchall()]
    print_comments_table(rows)


def main() -> None:
    """Главный цикл консольного меню."""
    print("=" * 50)
    print("  Лабораторная работа: Парсер форума и SQLite БД")
    print(f"  Файл базы данных: {DEFAULT_DB_FILE}")
    print("=" * 50)

    repo = DatabaseRepository(DEFAULT_DB_FILE)
    parser = ForumParser()

    menu = (
        "\nВыберите действие:\n"
        " 1. Загрузить и спарсить тему по URL\n"
        " 2. Загрузить посты из локального HTML-файла\n"
        " 3. Найти комментарий по ID\n"
        " 4. Найти комментарии автора по нику\n"
        " 5. Добавить комментарий вручную\n"
        " 6. Изменить текст комментария\n"
        " 7. Удалить комментарий\n"
        " 8. Показать все комментарии в базе\n"
        " 0. Выход\n"
        "> "
    )

    try:
        while True:
            choice = input(menu).strip()
            if choice == "1":
                parse_url_menu(parser, repo)
            elif choice == "2":
                parse_file_menu(parser, repo)
            elif choice == "3":
                get_by_id_menu(repo)
            elif choice == "4":
                get_by_name_menu(repo)
            elif choice == "5":
                add_comment_menu(repo)
            elif choice == "6":
                update_comment_menu(repo)
            elif choice == "7":
                delete_comment_menu(repo)
            elif choice == "8":
                show_all_comments_menu(repo)
            elif choice in ("0", "exit", "quit"):
                print("Выход из программы.")
                break
            else:
                print("Неизвестный пункт меню, попробуйте еще раз.")
    except (KeyboardInterrupt, EOFError):
        print("\nЗавершение работы программы.")
    finally:
        repo.close()


if __name__ == "__main__":
    main()
