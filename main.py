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
        force=True,  # сбрасывает ранее настроенные обработчики
    )
    logging.info("Логгер успешно сконфигурирован")
    logging.info("Приложение запущено")


def run_registration_flow(login, pwd, confirm_pwd):
    """Запускает валидацию и логирует результат."""
    masked_pwd = mask_password(pwd)
    masked_confirm = mask_password(confirm_pwd)
    params = f"Логин: '{login}', Пароль: {masked_pwd}, Подтверждение: {masked_confirm}"

    logging.debug(f"Попытка регистрации | {params}")

    try:
        if isinstance(login, int):
            logging.warning("Передан целочисленный логин, ожидается ошибка типа")

        status, message = validate_registration(login, pwd, confirm_pwd)

        if status:
            logging.info(f"Успешная регистрация | {params} | Результат: True")
        else:
            logging.warning(f"Ошибка валидации | {params} | Ошибка: '{message}' | Результат: False")

        print(f"Результат: {status}\nСообщение: '{message}'\n")
        return status, message

    except Exception as ex:
        # exception пишет ERROR вместе с traceback
        logging.exception(f"Сбой при обработке регистрации | {params}")
        print(f"Результат: False\nСообщение: 'Критическая ошибка: {ex}'\n")
        return False, str(ex)


def run_demo():
    print("=== ДЕМО-НАБОР ТЕСТОВ ===\n")

    test_cases = [
        # успешные
        ("+7-999-123-4567", "Пароль123!", "Пароль123!"),  # телефон
        ("user@mail.ru", "Секрет_2024#", "Секрет_2024#"),  # email
        ("ivan_ivanov", "МойПароль?99", "МойПароль?99"),  # строка
        # ошибки логина
        ("", "Пароль123!", "Пароль123!"),  # пустой логин
        ("admin", "Пароль123!", "Пароль123!"),  # черный список
        ("user", "Пароль123!", "Пароль123!"),  # короче 5 символов
        ("user-name!", "Пароль123!", "Пароль123!"),  # недопустимые символы
        ("+7-999-00", "Пароль123!", "Пароль123!"),  # неверный формат телефона
        # ошибки пароля
        ("valid_login", "", ""),  # пустой пароль
        ("valid_login", "Пароль123!", "Пароль999!"),  # не совпадают
        ("valid_login", "Пас1!", "Пас1!"),  # короче 7 символов
        ("valid_login", "Password123!", "Password123!"),  # латиница
        ("valid_login", "пароль123!", "пароль123!"),  # нет заглавной
        ("valid_login", "ПАРОЛЬ123!", "ПАРОЛЬ123!"),  # нет строчной
        ("valid_login", "ПарольБезЦифр!", "ПарольБезЦифр!"),  # нет цифры
        ("valid_login", "Пароль12345", "Пароль12345"),  # нет спецсимвола
    ]

    for login, pwd, confirm_pwd in test_cases:
        run_registration_flow(login, pwd, confirm_pwd)

    print("=== ДЕМОНСТРАЦИЯ TRACEBACK ===\n")

    # число вместо логина: AttributeError (у int нет .strip())
    run_registration_flow(89991234567, "Пароль123!", "Пароль123!")

    # число вместо пароля: TypeError (len(int))
    run_registration_flow("valid_login_two", 12345678, 12345678)


def run_manual():
    print("Ручной ввод. Для выхода введите q в поле логина.\n")
    while True:
        login = input("Логин: ")
        if login.lower() == "q":
            break
        pwd = input("Пароль: ")
        confirm_pwd = input("Подтверждение пароля: ")
        run_registration_flow(login, pwd, confirm_pwd)


def main():
    setup_logger()

    print("1 - демо-набор тестов")
    print("2 - ручной ввод")
    print("3 - и то и другое")
    mode = input("Выберите режим: ").strip()

    if mode in ("1", "3"):
        run_demo()
    if mode in ("2", "3"):
        run_manual()

    logging.info("Приложение завершило работу")


if __name__ == "__main__":
    main()