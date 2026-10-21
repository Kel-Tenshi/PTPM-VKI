"""точка входа приложения «Регистрация»

    python -m src.main          - интерактивная работа через консоль
    python src/main.py          - то же самое
    python -m src.main --demo   - прогон без ввода с клавиатуры
"""

import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# чтобы модуль запускался и как `python src/main.py`, и как `python -m src.main`,
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.controller import Controller
from src.database import DatabaseHandler
from src.external_service import EmailNotifier
from src.user_interface import ConsoleUserInterface, ScriptedUserInterface
from src.validator import RegistrationValidator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "file.log")
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "registration.db")

# сценарии для --demo: (описание, логин, пароль, подтверждение)
DEMO_SCENARIOS = (
    ("валидный пользователь, первый запрос", "ivan_petrov", "Пароль123!", "Пароль123!"),
    ("тот же пользователь повторно (кэш из БД)", "ivan_petrov", "Пароль123!", "Пароль123!"),
    ("невалидные данные (ошибка валидации)", "bad_user", "123", "123"),
)


def setup_logger(log_dir: Optional[str] = None, log_file: Optional[str] = None) -> str:
    """лог в консоль и в файл, возвращает путь к файлу"""
    log_dir = log_dir or LOG_DIR
    log_file = log_file or os.path.join(log_dir, "file.log")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | [%(levelname)-7s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8", mode="a"),
        ],
        force=True,
    )
    logging.info("Логгер успешно сконфигурирован")
    return log_file


def build_controller(db_path: Optional[str] = None) -> Controller:
    """контроллер на настоящих реализациях всех слоёв"""
    db_path = db_path or DB_PATH
    return Controller(
        validator=RegistrationValidator(),
        db_handler=DatabaseHandler(db_path),
        ui=ConsoleUserInterface(),
        external_service=EmailNotifier(),
    )


def format_result(result: Dict[str, Any]) -> str:
    """короткая сводка по результату"""
    return (
        f"логин='{result['login']}', статус={result['status']}, "
        f"источник={result['source']}, ошибка='{result['error_message']}', "
        f"отправлено внешнему сервису={result['sent_success']}"
    )


def run_interactive(db_path: Optional[str] = None) -> Dict[str, Any]:
    """полный сценарий с запросом данных у пользователя"""
    controller = build_controller(db_path)
    try:
        result = controller.run_pipeline()
    finally:
        controller.db_handler.close()

    logging.info("Итог операции: %s", format_result(result))
    print(f"Результат: {format_result(result)}")
    return result


def run_demo(db_path: str = ":memory:") -> None:
    """три сценария подряд, без клавиатуры"""
    db_handler = DatabaseHandler(db_path)
    try:
        for title, login, password, confirm_password in DEMO_SCENARIOS:
            logging.info("=== Сценарий: %s ===", title)
            ui = ScriptedUserInterface(login, password, confirm_password)
            controller = Controller(
                validator=RegistrationValidator(),
                db_handler=db_handler,
                ui=ui,
                external_service=EmailNotifier(),
            )
            result = controller.run_pipeline()
            logging.info("Итог сценария: %s", format_result(result))
    finally:
        db_handler.close()


def main(argv: Optional[List[str]] = None) -> int:
    """0 - успех, 1 - ошибка"""
    parser = argparse.ArgumentParser(
        description="Регистрация пользователя — Лабораторная работа №3"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="демонстрационный прогон без запроса ввода с клавиатуры",
    )
    args = parser.parse_args(argv)

    setup_logger()
    logging.info("Приложение запущено")
    try:
        if args.demo:
            run_demo()
        else:
            run_interactive()
    except Exception as ex:  # pragma: no cover
        logging.error("Необработанная ошибка приложения: %s", ex, exc_info=True)
        return 1

    logging.info("Приложение завершило работу штатно")
    return 0


if __name__ == "__main__":
    sys.exit(main())
