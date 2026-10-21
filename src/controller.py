"""контроллер: связывает слои в один сквозной сценарий"""

import logging
from typing import Any, Dict

from src.database import DatabaseHandler
from src.external_service import ExternalService
from src.user_interface import UserInterface
from src.validator import RegistrationValidator, mask_password

logger = logging.getLogger(__name__)


class Controller:
    """сквозной сценарий регистрации"""

    def __init__(
        self,
        validator: RegistrationValidator,
        db_handler: DatabaseHandler,
        ui: UserInterface,
        external_service: ExternalService,
    ):
        self.validator = validator
        self.db_handler = db_handler
        self.ui = ui
        self.external_service = external_service

    def run_pipeline(self) -> Dict[str, Any]:
        """спросить ввод -> взять из базы или посчитать -> отправить наружу"""

        # 1. ввод
        login, password, confirm_password = self.ui.get_user_input()

        # strip обязателен: валидатор чистит логин у себя, а в базу он уходит
        # ключом. Без этого "user" и " user " - две разные записи
        if isinstance(login, str):
            login = login.strip()

        logger.debug(
            "Запрос на регистрацию | Логин: '%s' | Пароль: %s",
            login,
            mask_password(password),
        )

        # 2. запись в базе
        cached_record = self.db_handler.get_record(login, password, confirm_password)

        if cached_record is None:
            # нет записи - считаем и сразу сохраняем
            status, error_msg = self.validator.validate(login, password, confirm_password)
            self.db_handler.add_record(login, password, confirm_password, status, error_msg)
            source = "calculated"
            logger.info(
                "Результат вычислен и сохранён в БД | Логин: '%s' | Статус: %s",
                login,
                status,
            )
        else:
            # запись есть - берём готовый результат
            status, error_msg = cached_record
            source = "database"
            logger.info(
                "Результат взят из БД (кэш) | Логин: '%s' | Статус: %s",
                login,
                status,
            )

        # 3. наружу уходит строка, а не структура
        result_str = f"User '{login}': status={status}, error='{error_msg}'"
        sent_success = self.external_service.send_data(result_str)
        if not sent_success:
            logger.warning("Не удалось отправить результат внешнему сервису | Логин: '%s'", login)

        # 4. результат
        return {
            "login": login,
            "status": status,
            "error_message": error_msg,
            "source": source,
            "result_str": result_str,
            "sent_success": sent_success,
        }
