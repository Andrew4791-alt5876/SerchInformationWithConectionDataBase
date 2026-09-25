from unittest.mock import Mock, patch

import pytest
import requests

from src.nominatim import NominatimClient


class TestNominatimClient:
    """Тесты для клиента Nominatim."""

    @pytest.fixture
    def client(self) -> NominatimClient:
        """Фикстура, создающая экземпляр клиента."""
        return NominatimClient()

    def test_init(self, client: NominatimClient) -> None:
        """Проверка инициализации клиента."""
        assert client.base_url == "https://nominatim.openstreetmap.org"
        assert client.endpoint == "/search"
        assert client.headers == {"User-Agent": "MyAircraftTracker/1.0 (tyrandr@list.ru)"}
        assert isinstance(client.session, type(requests.Session()))  # не импортировано, но можно проверить тип
        assert client._last_request_time == 0.0

    def test_rate_limit(self, client: NominatimClient) -> None:
        """Проверка ограничения частоты запросов: между вызовами должно быть не менее 1 секунды."""
        with patch("time.time") as mock_time, patch("time.sleep") as mock_sleep:
            # первый вызов: last_request_time = 0, разница >= 1, спим 0
            mock_time.return_value = 100.0
            client._last_request_time = 0.0
            client._rate_limit()
            mock_sleep.assert_not_called()
            assert client._last_request_time == 100.0

            # второй вызов: разница меньше 1 секунды (текущее время 100.5)
            mock_time.return_value = 100.5
            client._rate_limit()
            # должно быть вызвано time.sleep(1 - (100.5 - 100.0)) = 0.5
            mock_sleep.assert_called_once_with(0.5)
            assert client._last_request_time == 100.5

            # третий вызов: разница больше 1 секунды (101.8)
            mock_time.return_value = 101.8
            client._rate_limit()
            # спим 0
            assert mock_sleep.call_count == 1  # только один вызов sleep остаётся
            assert client._last_request_time == 101.8

    def test_get_data_success(self, client: NominatimClient) -> None:
        """get_data возвращает JSON при успешном запросе."""
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, "get", return_value=mock_response) as mock_get:
            result = client.get_data(params={"q": "test"})

        mock_get.assert_called_once_with("https://nominatim.openstreetmap.org/search", params={"q": "test"})
        assert result == {"test": "data"}

    def test_get_data_http_error(self, client: NominatimClient) -> None:
        """get_data пробрасывает исключение при HTTP ошибке."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")

        with patch.object(client.session, "get", return_value=mock_response):
            with pytest.raises(requests.exceptions.HTTPError):
                client.get_data()

    def test_get_country_coordinates_single_country(self, client: NominatimClient) -> None:
        """Для одной страны возвращается список с boundingbox."""
        mock_data = [{"boundingbox": ["40.0", "50.0", "20.0", "30.0"]}]

        with patch.object(client, "_make_request", return_value=mock_data) as mock_request:
            result = client.get_country_coordinates(["Russia"])

        mock_request.assert_called_once_with(
            "search", {"q": "Russia", "format": "json", "limit": 1}, headers=client.headers
        )
        assert result == [["40.0", "50.0", "20.0", "30.0"]]

    def test_get_country_coordinates_multiple_countries(self, client: NominatimClient) -> None:
        """
        При нескольких странах возвращается только первый (из-за бага в коде).
        В текущей реализации return находится внутри цикла, поэтому обрабатывается только первая страна.
        """
        mock_data1 = [{"boundingbox": ["box1"]}]
        mock_data2 = [{"boundingbox": ["box2"]}]

        with patch.object(client, "_make_request", side_effect=[mock_data1, mock_data2]) as mock_request:
            result = client.get_country_coordinates(["Russia", "USA"])

        # Должен быть вызван только один раз, так как после первого return функция завершается
        mock_request.assert_called_once_with(
            "search", {"q": "Russia", "format": "json", "limit": 1}, headers=client.headers
        )
        assert result == [["box1"]]

    def test_get_country_coordinates_empty_list_input(self, client: NominatimClient) -> None:
        """При пустом списке стран возвращается пустой список."""
        with patch.object(client, "_make_request") as mock_request:
            result = client.get_country_coordinates([])

        mock_request.assert_not_called()
        assert result == []

    def test_get_country_coordinates_network_error(self, client: NominatimClient) -> None:
        """При ошибке запроса (возвращается строка) возвращается пустой список."""
        with patch.object(client, "_make_request", return_value="Проверьте соединение с интернетом!"):
            result = client.get_country_coordinates(["Russia"])

        assert result == []

    def test_get_country_coordinates_index_error(self, client: NominatimClient) -> None:
        """Если API вернул пустой список (нет данных), возвращается пустой список."""
        with patch.object(client, "_make_request", return_value=[]):
            result = client.get_country_coordinates(["Russia"])

        assert result == []

    def test_get_country_coordinates_key_error(self, client: NominatimClient) -> None:
        """Если в ответе нет ключа 'boundingbox', возвращается пустой список."""
        with patch.object(client, "_make_request", return_value=[{"other": "data"}]):
            result = client.get_country_coordinates(["Russia"])

        assert result == []

    def test_get_country_coordinates_multiple_errors(self, client: NominatimClient) -> None:
        """
        Если для нескольких стран первая возвращает ошибку, функция завершится с пустым списком.
        (из-за раннего return в except)
        """
        with patch.object(client, "_make_request", side_effect=ValueError):
            result = client.get_country_coordinates(["Russia", "USA"])

        assert result == []
