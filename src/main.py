import logging
import os
import sys

from validator import mask_password, validate_registration

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "file.log")


def setup_logger():
    """Логирование параллельно в консоль и в файл."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | [%(levelname)-7s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a"),
        ],
        force=True,
    )
    logging.info("Логгер успешно сконфигурирован")
    logging.info("Приложение запущено")


def run_registration_flow(login, pwd, confirm_pwd):
    """
    Запускает валидацию и корректно логирует результат:
    - INFO: успешная регистрация или штатный отказ валидации.
    - WARNING: потенциальные проблемы в будущем (например, верхний регистр в логине).
    - ERROR: внутренний сбой функции при необработанном исключении.
    """
    masked_pwd = mask_password(pwd)
    masked_confirm = mask_password(confirm_pwd)
    params = f"Логин: '{login}', Пароль: {masked_pwd}, Подтверждение: {masked_confirm}"

    logging.debug(f"Попытка регистрации | {params}")

    try:
        # Пример WARNING: логин валиден сейчас, но верхний регистр может вызвать проблемы в БД в будущем
        if isinstance(login, str) and any(c.isupper() for c in login) and "@" not in login and not login.startswith("+"):
            logging.warning(
                f"Логин содержит заглавные символы: возможен риск коллизий при регистронезависимом поиске | {params}"
            )

        status, message = validate_registration(login, pwd, confirm_pwd)

        if status:
            logging.info(f"Успешная регистрация | {params} | Результат: True")
        else:
            # Штатная ситуация (пользователь ошибся при вводе) -> логируем INFO, а не WARNING/ERROR
            logging.info(
                f"Отказ в регистрации (бизнес-валидация не пройдена) | {params} | Причина: '{message}' | Результат: False"
            )

        return status, message

    except Exception as ex:
        # Ошибка, которая прервала выполнение функционала
        logging.error(f"Сбой при обработке регистрации | {params} | Исключение: {ex}", exc_info=True)
        return False, str(ex)


def main():
    setup_logger()
    logging.info("Демонстрация работы приложения")
    run_registration_flow("user_test", "Пароль123!", "Пароль123!")
    run_registration_flow("User_Test", "Пароль123!", "Пароль123!")  # вызовет WARNING
    run_registration_flow("user_test", "123", "123")  # вызовет INFO об отказе
    logging.info("Приложение завершило работу штатно")


if __name__ == "__main__":
    main()