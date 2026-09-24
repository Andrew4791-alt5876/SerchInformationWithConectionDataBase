from abc import ABC, abstractmethod
from typing import Any, Optional, cast

import requests


class APIClient(ABC):
    """
    Абстрактный класс для работы с внешними API.
    Определяет общий интерфейс и базовый метод выполнения HTTP-запросов.
    """

    def __init__(self, base_url: str = "", endpoint: str = "") -> None:
        self.base_url = base_url
        self.endpoint = endpoint
        self.session = requests.Session()

    @abstractmethod
    def get_data(self, params: Optional[dict[Any, Any]] = None) -> dict[Any, Any]:
        url = f"{self.base_url}{self.endpoint}"  # предположим, endpoint задан
        response = self.session.get(url, params=params)  # здесь создаётся response
        response.raise_for_status()
        return cast(dict[Any, Any], response.json())

    def _make_request(
        self, endpoint: str, params: Optional[dict[str, Any]] = None, headers: Optional[dict[str, Any]] = None
    ) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return "Проверьте соединение с интернетом!"
