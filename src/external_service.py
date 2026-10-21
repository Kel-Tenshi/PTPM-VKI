"""имитация стороннего сервиса"""

from abc import ABC, abstractmethod


class ExternalService(ABC):
    """интерфейс внешнего сервиса"""

    @abstractmethod
    def send_data(self, data: str) -> bool:
        """отправляет строку наружу, True - если ушло"""
        raise NotImplementedError


class EmailNotifier(ExternalService):
    """отправки по-настоящему нет, только имитация"""

    def send_data(self, data: str) -> bool:
        print(f"[EXTERNAL SERVER SIMULATION] Sending: {data}")
        return True
