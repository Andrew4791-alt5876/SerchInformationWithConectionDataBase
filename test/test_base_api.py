from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

import pytest
import requests

from src.base_api import APIClient


class ConcreteAPIClient(APIClient):
    """Конкретная реализация для тестирования методов базового класса."""

    def get_data(self, params: Optional[Dict[Any, Any]] = None) -> Dict[Any, Any]:
        # Используем _make_request для демонстрации
        return self._make_request(self.endpoint, params)  # type: ignore[no-any-return]


class TestAPIClient:
    """Тесты для абстрактного класса APIClient."""

    def test_abstract_class_cannot_be_instantiated(self) -> None:
        """Проверка, что абстрактный класс нельзя создать напрямую."""
        with pytest.raises(TypeError):
            APIClient()  # type: ignore[abstract]

    def test_get_data_is_abstract(self) -> None:
        """Метод get_data должен быть абстрактным."""
        assert hasattr(APIClient.get_data, "__isabstractmethod__")

    def test_make_request_success(self) -> None:
        """Успешный запрос возвращает JSON-ответ."""
        client = ConcreteAPIClient(base_url="https://api.example.com", endpoint="/test")
        mock_response = Mock()
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = client._make_request(
                endpoint="subpath", params={"param": 1}, headers={"Authorization": "Bearer token"}
            )

        mock_get.assert_called_once_with(
            "https://api.example.com/subpath",
            params={"param": 1},
            headers={"Authorization": "Bearer token"},
            timeout=10,
        )
        assert result == {"key": "value"}

    def test_make_request_removes_leading_slash(self) -> None:
        """Метод корректно обрабатывает endpoint, начинающийся со слэша."""
        client = ConcreteAPIClient(base_url="https://api.example.com")
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}

        with patch("requests.get", return_value=mock_response) as mock_get:
            client._make_request("/users")

        mock_get.assert_called_once_with("https://api.example.com/users", params=None, headers=None, timeout=10)

    def test_make_request_handles_request_exception(self) -> None:
        """При сетевой ошибке возвращается текст с предложением проверить соединение."""
        client = ConcreteAPIClient()

        with patch("requests.get", side_effect=requests.RequestException("Connection error")):
            result = client._make_request("some")

        assert result == "Проверьте соединение с интернетом!"

    def test_make_request_handles_http_error(self) -> None:
        """При HTTP ошибке (raise_for_status) также возвращается текст."""
        client = ConcreteAPIClient()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch("requests.get", return_value=mock_response):
            result = client._make_request("some")

        assert result == "Проверьте соединение с интернетом!"

    def test_make_request_timeout_is_set(self) -> None:
        """Проверка, что timeout=10 передаётся в вызов requests.get."""
        client = ConcreteAPIClient()
        mock_response = Mock()
        mock_response.json.return_value = {}

        with patch("requests.get", return_value=mock_response) as mock_get:
            client._make_request("data")

        _, kwargs = mock_get.call_args
        assert kwargs.get("timeout") == 10
