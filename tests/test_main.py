"""тесты точки входа (src/main.py)"""

import logging
import os
import tempfile
import unittest
from unittest.mock import patch

import src.main as main_module
from src.controller import Controller
from src.database import DatabaseHandler
from src.external_service import EmailNotifier
from src.user_interface import ConsoleUserInterface
from src.validator import RegistrationValidator


class LogCleanupMixin:
    """закрывает хэндлеры логгера

    на винде открытый файл нельзя удалить, и временная папка не смогла бы
    очиститься в конце теста
    """

    def close_log_handlers(self):
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            handler.close()

    def tearDown(self):
        self.close_log_handlers()


# -логгер-
class TestSetupLogger(LogCleanupMixin, unittest.TestCase):
    """настройка логирования"""

    def test_setup_logger_creates_log_file(self):
        # логгер создаёт файл и пишет в него
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                log_file = main_module.setup_logger(log_dir=tmp_dir)
                self.assertTrue(os.path.isfile(log_file))

                logging.info("пробная запись в лог")
                for handler in logging.getLogger().handlers:
                    if isinstance(handler, logging.FileHandler):
                        handler.flush()

                with open(log_file, encoding="utf-8") as file:
                    content = file.read()
                self.assertIn("пробная запись в лог", content)
                self.assertIn("Логгер успешно сконфигурирован", content)
            finally:
                self.close_log_handlers()


# -сборка контроллера-
class TestBuildController(LogCleanupMixin, unittest.TestCase):
    """контроллер собирается из настоящих компонентов"""

    def test_build_controller_wires_real_components(self):
        # вместо моков - настоящие реализации всех четырёх слоёв
        with tempfile.TemporaryDirectory() as tmp_dir:
            controller = main_module.build_controller(
                db_path=os.path.join(tmp_dir, "registration.db")
            )
            try:
                self.assertIsInstance(controller, Controller)
                self.assertIsInstance(controller.validator, RegistrationValidator)
                self.assertIsInstance(controller.db_handler, DatabaseHandler)
                self.assertIsInstance(controller.ui, ConsoleUserInterface)
                self.assertIsInstance(controller.external_service, EmailNotifier)
            finally:
                controller.db_handler.close()


# -сводка результата-
class TestFormatResult(unittest.TestCase):
    """формат сводки"""

    def test_format_result_contains_key_fields(self):
        result = {
            "login": "ivan_petrov",
            "status": True,
            "error_message": "",
            "source": "calculated",
            "result_str": "User 'ivan_petrov': status=True, error=''",
            "sent_success": True,
        }
        summary = main_module.format_result(result)
        self.assertIn("ivan_petrov", summary)
        self.assertIn("calculated", summary)


# -запуск приложения-
class TestMain(LogCleanupMixin, unittest.TestCase):
    """main()"""

    def test_main_demo_mode_runs_without_console_input(self):
        # демо отрабатывает целиком и клавиатуру не трогает
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                with patch.object(main_module, "LOG_DIR", tmp_dir):
                    with patch(
                        "builtins.input",
                        side_effect=AssertionError("в демо-режиме input() не вызывается"),
                    ):
                        exit_code = main_module.main(["--demo"])

                self.assertEqual(exit_code, 0)
                log_file = os.path.join(tmp_dir, "file.log")
                self.assertTrue(os.path.isfile(log_file))
                with open(log_file, encoding="utf-8") as file:
                    content = file.read()
                self.assertIn("Приложение запущено", content)
                self.assertIn("Приложение завершило работу штатно", content)
            finally:
                self.close_log_handlers()

    def test_main_interactive_mode_uses_console_input(self):
        # интерактивный режим спрашивает данные и пишет в файловую базу
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                db_path = os.path.join(tmp_dir, "registration.db")
                with patch.object(main_module, "LOG_DIR", tmp_dir):
                    with patch.object(main_module, "DB_PATH", db_path):
                        with patch(
                            "builtins.input",
                            side_effect=["ivan_petrov", "Пароль123!", "Пароль123!"],
                        ):
                            exit_code = main_module.main([])

                self.assertEqual(exit_code, 0)
                self.assertTrue(os.path.isfile(db_path))

                db = DatabaseHandler(db_path)
                try:
                    self.assertEqual(
                        db.get_record("ivan_petrov", "Пароль123!", "Пароль123!"),
                        (True, ""),
                    )
                finally:
                    db.close()
            finally:
                self.close_log_handlers()

    def test_main_returns_error_code_on_unhandled_exception(self):
        # необработанная ошибка: в лог ERROR, код возврата 1
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                with patch.object(main_module, "LOG_DIR", tmp_dir):
                    with patch.object(
                        main_module, "run_interactive", side_effect=RuntimeError("сбой сценария")
                    ):
                        exit_code = main_module.main([])

                self.assertEqual(exit_code, 1)
                log_file = os.path.join(tmp_dir, "file.log")
                with open(log_file, encoding="utf-8") as file:
                    content = file.read()
                self.assertIn("Необработанная ошибка приложения", content)
            finally:
                self.close_log_handlers()


if __name__ == "__main__":
    unittest.main()
