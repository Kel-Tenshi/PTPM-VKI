import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.controller import Controller
from src.database import DatabaseHandler
from src.external_service import EmailNotifier, ExternalService
from src.user_interface import ConsoleUserInterface, ScriptedUserInterface, UserInterface
from src.validator import RegistrationValidator


# -база, модульные-
class TestDatabaseHandler(unittest.TestCase):
    """работа с базой в памяти"""

    def setUp(self):
        self.db = DatabaseHandler(":memory:")
        self.addCleanup(self.db.close)

    def test_record_is_absent_before_adding(self):
        # до добавления записи нет
        self.assertIsNone(self.db.get_record("user1", "Пароль123!", "Пароль123!"))

    def test_add_then_get_record(self):
        # добавили - читаем по той же тройке
        self.db.add_record("user1", "Пароль123!", "Пароль123!", True, "")
        self.assertEqual(self.db.get_record("user1", "Пароль123!", "Пароль123!"), (True, ""))

    def test_add_record_replaces_existing_record(self):
        # тот же ключ перезаписывает
        self.db.add_record("user1", "Пароль123!", "Пароль123!", True, "")
        self.db.add_record("user1", "Пароль123!", "Пароль123!", False, "ошибка")
        self.assertEqual(
            self.db.get_record("user1", "Пароль123!", "Пароль123!"),
            (False, "ошибка"),
        )

    def test_delete_record_removes_it(self):
        # удаление существующей записи
        self.db.add_record("user1", "Пароль123!", "Пароль123!", True, "")
        self.assertTrue(self.db.delete_record("user1", "Пароль123!", "Пароль123!"))
        self.assertIsNone(self.db.get_record("user1", "Пароль123!", "Пароль123!"))

    def test_delete_missing_record_returns_false(self):
        # удалять нечего
        self.assertFalse(self.db.delete_record("nobody", "Пароль123!", "Пароль123!"))

    def test_count_records_reflects_table_state(self):
        # счётчик считает записи
        self.assertEqual(self.db.count_records(), 0)
        self.db.add_record("user1", "Пароль123!", "Пароль123!", True, "")
        self.assertEqual(self.db.count_records(), 1)

    def test_close_releases_connection(self):
        # после close() база закрыта
        self.db.close()
        with self.assertRaises(sqlite3.ProgrammingError):
            self.db.get_record("user1", "Пароль123!", "Пароль123!")


# -база, интеграционные-
class TestDatabaseIntegration(unittest.TestCase):
    """файловая база и два независимых обработчика"""

    def test_record_survives_between_two_handlers(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "registration.db")

            first = DatabaseHandler(db_path)
            first.add_record("ivan_petrov", "Пароль123!", "Пароль123!", True, "")
            first.close()

            second = DatabaseHandler(db_path)
            try:
                self.assertEqual(
                    second.get_record("ivan_petrov", "Пароль123!", "Пароль123!"),
                    (True, ""),
                )
            finally:
                second.close()

    def test_table_is_created_automatically_in_missing_folder(self):
        # папка под файл базы создаётся сама
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "nested", "folder", "registration.db")
            db = DatabaseHandler(db_path)
            try:
                self.assertTrue(os.path.isfile(db_path))
                self.assertEqual(db.count_records(), 0)
            finally:
                db.close()


# -ввод, модульные-
class TestUserInterface(unittest.TestCase):
    """интерфейс ввода"""

    def test_console_interface_reads_three_answers(self):
        # спрашивает логин, пароль и подтверждение
        with patch(
            "builtins.input", side_effect=["ivan_petrov", "Пароль123!", "Пароль123!"]
        ) as mock_input:
            ui = ConsoleUserInterface()
            self.assertEqual(
                ui.get_user_input(),
                ("ivan_petrov", "Пароль123!", "Пароль123!"),
            )
        self.assertEqual(mock_input.call_count, 3)

    def test_abstract_interface_cannot_be_instantiated(self):
        # интерфейс нельзя создать
        with self.assertRaises(TypeError):
            UserInterface()

    def test_base_implementation_raises_not_implemented(self):
        # у базового метода реализации нет
        with self.assertRaises(NotImplementedError):
            UserInterface.get_user_input(None)

    def test_scripted_interface_returns_prepared_answers(self):
        # заглушка отдаёт заготовку и клавиатуру не трогает
        ui = ScriptedUserInterface("ivan_petrov", "Пароль123!", "Пароль123!")
        self.assertEqual(
            ui.get_user_input(),
            ("ivan_petrov", "Пароль123!", "Пароль123!"),
        )


# -внешний сервис, модульные-
class TestExternalService(unittest.TestCase):
    """имитация отправки наружу"""

    def test_email_notifier_reports_success(self):
        # отправка всегда успешна
        with patch("builtins.print") as mock_print:
            self.assertTrue(EmailNotifier().send_data("User 'ivan_petrov': status=True"))
        mock_print.assert_called_once()

    def test_email_notifier_passes_data_to_output(self):
        # наружу уходит ровно та строка, которую дали
        with patch("builtins.print") as mock_print:
            EmailNotifier().send_data("payload-42")
        self.assertIn("payload-42", mock_print.call_args[0][0])

    def test_abstract_external_service_cannot_be_instantiated(self):
        # интерфейс нельзя создать
        with self.assertRaises(TypeError):
            ExternalService()

    def test_base_implementation_raises_not_implemented(self):
        # у базового метода реализации нет
        with self.assertRaises(NotImplementedError):
            ExternalService.send_data(None, "payload")


# -контроллер в полной изоляции-
class TestControllerUnit(unittest.TestCase):
    """все зависимости - моки, базы и внешнего сервиса тут нет"""

    def setUp(self):
        self.validator = MagicMock(spec=RegistrationValidator)
        self.db = MagicMock(spec=DatabaseHandler)
        self.ui = MagicMock(spec=UserInterface)
        self.external = MagicMock(spec=ExternalService)

        self.ui.get_user_input.return_value = ("mock_user", "Пароль123!", "Пароль123!")
        self.db.get_record.return_value = None
        self.validator.validate.return_value = (True, "")
        self.external.send_data.return_value = True

        self.controller = Controller(self.validator, self.db, self.ui, self.external)

    def test_pipeline_calculates_result_when_record_is_missing(self):
        # записи нет - считаем и пишем в базу
        result = self.controller.run_pipeline()

        self.validator.validate.assert_called_once_with(
            "mock_user", "Пароль123!", "Пароль123!"
        )
        self.db.add_record.assert_called_once_with(
            "mock_user", "Пароль123!", "Пароль123!", True, ""
        )
        self.assertEqual(result["source"], "calculated")
        self.assertTrue(result["status"])

    def test_pipeline_uses_cached_record_when_it_exists(self):
        # запись есть - валидатор не трогаем, берём готовое
        self.db.get_record.return_value = (False, "cached_error")

        result = self.controller.run_pipeline()

        self.validator.validate.assert_not_called()
        self.db.add_record.assert_not_called()
        self.assertEqual(result["source"], "database")
        self.assertEqual(result["error_message"], "cached_error")
        self.assertFalse(result["status"])

    def test_pipeline_sends_result_string_to_external_service(self):
        # наружу уходит строка-результат
        self.controller.run_pipeline()
        self.external.send_data.assert_called_once_with(
            "User 'mock_user': status=True, error=''"
        )

    def test_pipeline_reports_external_service_failure(self):
        # сбой отправки попадает в результат, а не теряется
        self.external.send_data.return_value = False
        result = self.controller.run_pipeline()
        self.assertFalse(result["sent_success"])

    def test_pipeline_returns_all_result_fields(self):
        # результат содержит все поля
        result = self.controller.run_pipeline()
        self.assertEqual(
            set(result.keys()),
            {
                "login",
                "status",
                "error_message",
                "source",
                "result_str",
                "sent_success",
            },
        )


# -сквозные сценарии-
class TestPipelineIntegration(unittest.TestCase):
    """настоящая база и настоящий валидатор, заглушки только на границах"""

    def setUp(self):
        self.db = DatabaseHandler(":memory:")
        self.addCleanup(self.db.close)

        self.validator = RegistrationValidator()
        self.external = MagicMock(spec=ExternalService)
        self.external.send_data.return_value = True

    def _run_pipeline(self, login, password, confirm_password):
        """прогон сценария, ввод заглушен"""
        with patch("builtins.input", side_effect=[login, password, confirm_password]):
            controller = Controller(
                self.validator, self.db, ConsoleUserInterface(), self.external
            )
            return controller.run_pipeline()

    def test_valid_registration_is_calculated_saved_and_sent(self):
        # успех: посчитали, записали в базу, отправили наружу
        result = self._run_pipeline("ivan_petrov", "Пароль123!", "Пароль123!")

        self.assertTrue(result["status"])
        self.assertEqual(result["source"], "calculated")
        self.assertEqual(result["error_message"], "")
        self.assertEqual(
            self.db.get_record("ivan_petrov", "Пароль123!", "Пароль123!"), (True, "")
        )
        self.external.send_data.assert_called_once_with(
            "User 'ivan_petrov': status=True, error=''"
        )

    def test_repeated_request_is_served_from_database(self):
        # повтор - из базы, без пересчёта
        first = self._run_pipeline("ivan_petrov", "Пароль123!", "Пароль123!")
        second = self._run_pipeline("ivan_petrov", "Пароль123!", "Пароль123!")

        self.assertEqual(first["source"], "calculated")
        self.assertEqual(second["source"], "database")
        self.assertEqual(second["status"], first["status"])
        self.assertEqual(second["error_message"], first["error_message"])
        self.assertEqual(self.db.count_records(), 1)

    def test_failed_validation_is_stored_in_db_and_reported(self):
        # отказ сохраняем в базу и отправляем наружу
        result = self._run_pipeline("bad_user", "123", "123")

        self.assertFalse(result["status"])
        self.assertEqual(result["source"], "calculated")
        self.assertNotEqual(result["error_message"], "")

        stored = self.db.get_record("bad_user", "123", "123")
        self.assertIsNotNone(stored)
        self.assertFalse(stored[0])
        self.assertEqual(stored[1], result["error_message"])

        self.external.send_data.assert_called_once()
        self.assertIn(result["error_message"], self.external.send_data.call_args[0][0])

    def test_cached_value_is_used_even_if_validator_would_agree_differently(self):
        # кэш важнее пересчёта: валидатор не вызывается
        self.db.add_record("cached_user", "Пароль123!", "Пароль123!", False, "ошибка из кэша")
        validator_spy = MagicMock(wraps=self.validator)

        with patch("builtins.input", side_effect=["cached_user", "Пароль123!", "Пароль123!"]):
            controller = Controller(
                validator_spy, self.db, ConsoleUserInterface(), self.external
            )
            result = controller.run_pipeline()

        self.assertEqual(result["source"], "database")
        self.assertEqual(result["error_message"], "ошибка из кэша")
        self.assertFalse(result["status"])
        validator_spy.validate.assert_not_called()

    def test_pipeline_survives_external_service_failure(self):
        # сбой внешнего сервиса сценарий не ломает
        self.external.send_data.return_value = False
        result = self._run_pipeline("ivan_petrov", "Пароль123!", "Пароль123!")

        self.assertTrue(result["status"])
        self.assertFalse(result["sent_success"])

    def test_login_is_normalized_before_it_reaches_database(self):
        # логин с пробелами чистится один раз: в базе, в результате и
        # в строке наружу должен быть один и тот же вариант
        result = self._run_pipeline("  ivan_petrov  ", "Пароль123!", "Пароль123!")

        self.assertTrue(result["status"])
        self.assertEqual(result["login"], "ivan_petrov")
        self.assertEqual(
            self.db.get_record("ivan_petrov", "Пароль123!", "Пароль123!"), (True, "")
        )
        self.assertIsNone(self.db.get_record("  ivan_petrov  ", "Пароль123!", "Пароль123!"))
        self.external.send_data.assert_called_once_with(
            "User 'ivan_petrov': status=True, error=''"
        )

    def test_repeated_request_with_spaces_hits_the_cache(self):
        # один и тот же человек с пробелами и без - одна запись и кэш
        self._run_pipeline("ivan_petrov", "Пароль123!", "Пароль123!")
        second = self._run_pipeline("  ivan_petrov ", "Пароль123!", "Пароль123!")

        self.assertEqual(second["source"], "database")
        self.assertEqual(self.db.count_records(), 1)

    def test_non_string_login_is_reported_as_validation_error(self):
        # нестроковый логин не роняет сценарий, а даёт сообщение
        result = self._run_pipeline(89991234567, "Пароль123!", "Пароль123!")

        self.assertFalse(result["status"])
        self.assertIn("должен быть строкой", result["error_message"])
        self.assertEqual(result["source"], "calculated")

    def test_full_stack_with_real_notifier_and_scripted_ui(self):
        # все слои настоящие, заглушка только на вводе
        ui = ScriptedUserInterface("ivan_petrov", "Пароль123!", "Пароль123!")
        controller = Controller(self.validator, self.db, ui, EmailNotifier())

        with patch("builtins.print") as mock_print:
            result = controller.run_pipeline()

        self.assertTrue(result["status"])
        self.assertTrue(result["sent_success"])
        self.assertEqual(result["source"], "calculated")
        printed = " ".join(str(call) for call in mock_print.call_args_list)
        self.assertIn("ivan_petrov", printed)


if __name__ == "__main__":
    unittest.main()
