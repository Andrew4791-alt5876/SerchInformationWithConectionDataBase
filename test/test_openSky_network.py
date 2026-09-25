from unittest.mock import Mock, call, patch

import pytest
import requests
from _pytest.capture import CaptureFixture

from src.openSky_network import OpenSkyClient


class TestOpenSkyClient:
    """Тесты для класса OpenSkyClient."""

    @pytest.fixture
    def client(self) -> OpenSkyClient:
        """Фикстура с экземпляром клиента."""
        return OpenSkyClient()

    def test_init(self, client: OpenSkyClient) -> None:
        """Проверка инициализации."""
        assert client.base_url == "https://opensky-network.org/api"
        assert client.endpoint == "/states/all"
        assert isinstance(client.session, requests.Session)

    def test_get_data_success(self, client: OpenSkyClient) -> None:
        """get_data возвращает JSON при успешном запросе."""
        mock_response = Mock()
        mock_response.json.return_value = {"states": [["abc123"]]}
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, "get", return_value=mock_response) as mock_get:
            result = client.get_data(params={"lamin": 10, "lamax": 20})

        mock_get.assert_called_once_with(
            "https://opensky-network.org/api/states/all", params={"lamin": 10, "lamax": 20}
        )
        assert result == {"states": [["abc123"]]}

    def test_get_data_http_error(self, client: OpenSkyClient) -> None:
        """get_data пробрасывает исключение при HTTP ошибке."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")

        with patch.object(client.session, "get", return_value=mock_response):
            with pytest.raises(requests.exceptions.HTTPError):
                client.get_data()

    def test_get_aircraft_in_bbox_empty_coords(self, client: OpenSkyClient, capsys: CaptureFixture[str]) -> None:
        """Если список координат пуст, выводится сообщение и возвращается пустой список."""
        result = client.get_aircraft_in_bbox([])
        captured = capsys.readouterr()
        assert "В запросе отсутствуют координаты страны!" in captured.out
        assert result == []

    def test_get_aircraft_in_bbox_single_bbox(self, client: OpenSkyClient) -> None:
        """Один bounding box – выполняется один запрос, возвращаются данные."""
        mock_data = {"states": [["abc123"], ["def456"]]}
        with patch.object(client, "get_data", return_value=mock_data) as mock_get:
            result = client.get_aircraft_in_bbox([["10", "20", "30", "40"]])

        mock_get.assert_called_once_with(params={"lamin": "10", "lamax": "20", "lomin": "30", "lomax": "40"})
        assert result == [["abc123"], ["def456"]]

    def test_get_aircraft_in_bbox_multiple_bboxes(self, client: OpenSkyClient) -> None:
        """Несколько bounding boxes – последовательные запросы, данные агрегируются."""
        mock_responses = [{"states": [["a1"], ["a2"]]}, {"states": [["b1"]]}]
        with patch.object(client, "get_data", side_effect=mock_responses) as mock_get:
            result = client.get_aircraft_in_bbox([["10", "20", "30", "40"], ["50", "60", "70", "80"]])

        expected_calls = [
            call(params={"lamin": "10", "lamax": "20", "lomin": "30", "lomax": "40"}),
            call(params={"lamin": "50", "lamax": "60", "lomin": "70", "lomax": "80"}),
        ]
        mock_get.assert_has_calls(expected_calls)
        assert result == [["a1"], ["a2"], ["b1"]]

    def test_get_aircraft_in_bbox_with_sleep(self, client: OpenSkyClient) -> None:
        """Между запросами вызывается time.sleep(1) после каждого запроса."""
        mock_data = {"states": [["test"]]}
        with patch.object(client, "get_data", return_value=mock_data) as mock_get, patch("time.sleep") as mock_sleep:
            result = client.get_aircraft_in_bbox([["1", "2", "3", "4"], ["5", "6", "7", "8"]])
        mock_get.assert_called()
        # Для двух bbox ожидаем два вызова sleep(1)
        expected_calls = [call(1), call(1)]
        mock_sleep.assert_has_calls(expected_calls)
        assert mock_sleep.call_count == 2
        assert result == [["test"], ["test"]]

    def test_get_aircraft_in_bbox_exception_handling(self, client: OpenSkyClient) -> None:
        """При возникновении исключения возвращается пустой список."""
        with patch.object(client, "get_data", side_effect=Exception("API error")):
            result = client.get_aircraft_in_bbox([["10", "20", "30", "40"]])
            assert result == []

    def test_get_aircraft_in_bbox_exception_during_second_request(self, client: OpenSkyClient) -> None:
        """Исключение во втором запросе прерывает выполнение и возвращает пустой список."""
        mock_responses = [{"states": [["first"]]}, Exception("Second request failed")]
        with patch.object(client, "get_data", side_effect=mock_responses):
            result = client.get_aircraft_in_bbox([["1", "2", "3", "4"], ["5", "6", "7", "8"]])
            assert result == []
