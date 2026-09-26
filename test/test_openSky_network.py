from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
import requests

from src.openSky_network import OpenSkyClient

# ---------- фикстуры ----------


@pytest.fixture
def session() -> Any:
    """Мок requests.Session. Any — чтобы mypy не проверял атрибуты мока."""
    return MagicMock()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, session: Any) -> OpenSkyClient:
    """OpenSkyClient с замоканным requests.Session и заглушённым sleep."""
    monkeypatch.setattr("time.sleep", lambda _: None)
    c = OpenSkyClient()
    monkeypatch.setattr(c, "session", session)
    return c


@pytest.fixture
def bbox() -> list[float]:
    """Bounding box Германии: [lamin, lamax, lomin, lomax]."""
    return [47.27, 55.06, 5.87, 15.04]


def make_response(json_data: Any, status_ok: bool = True) -> Any:
    """Фейковый requests.Response."""
    response = MagicMock()
    response.json.return_value = json_data
    if status_ok:
        response.raise_for_status.return_value = None
    else:
        response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    return response


# ---------- инициализация ----------


class TestOpenSkyClientInit:
    def test_default_endpoint(self) -> None:
        c = OpenSkyClient()
        assert c.endpoint == "/states/all"

    def test_custom_endpoint(self) -> None:
        c = OpenSkyClient(endpoint="/states/other")
        assert c.endpoint == "/states/other"

    def test_base_url(self) -> None:
        c = OpenSkyClient()
        assert c.base_url == "https://opensky-network.org/api"


# ---------- get_data ----------


class TestOpenSkyClientGetData:
    def test_calls_correct_url(self, client: OpenSkyClient, session: Any) -> None:
        session.get.return_value = make_response({"states": []})
        client.get_data()
        session.get.assert_called_once_with(
            "https://opensky-network.org/api/states/all",
            params=None,
        )

    def test_passes_params(self, client: OpenSkyClient, session: Any) -> None:
        session.get.return_value = make_response({"states": []})
        params = {"lamin": 47.27, "lamax": 55.06}
        client.get_data(params=params)
        session.get.assert_called_once_with(
            "https://opensky-network.org/api/states/all",
            params=params,
        )

    def test_returns_json(self, client: OpenSkyClient, session: Any) -> None:
        payload = {"time": 1700000000, "states": [["abc"]]}
        session.get.return_value = make_response(payload)
        result = client.get_data()
        assert result == payload

    def test_raises_for_status(self, client: OpenSkyClient, session: Any) -> None:
        session.get.return_value = make_response({}, status_ok=False)
        with pytest.raises(requests.HTTPError):
            client.get_data()

    def test_propagates_connection_error(self, client: OpenSkyClient, session: Any) -> None:
        session.get.side_effect = requests.ConnectionError("no network")
        with pytest.raises(requests.ConnectionError):
            client.get_data()


# ---------- get_aircraft_in_bbox: пустые координаты ----------


class TestGetAircraftInBboxEmptyCoords:
    def test_empty_list_returns_empty(self, client: OpenSkyClient, session: Any) -> None:
        assert client.get_aircraft_in_bbox([]) == []

    def test_empty_list_does_not_call_api(self, client: OpenSkyClient, session: Any) -> None:
        client.get_aircraft_in_bbox([])
        session.get.assert_not_called()

    def test_empty_list_prints_message(
        self,
        client: OpenSkyClient,
        session: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        client.get_aircraft_in_bbox([])
        out = capsys.readouterr().out
        assert "отсутствуют координаты" in out


# ---------- get_aircraft_in_bbox: успешные сценарии ----------


class TestGetAircraftInBboxSuccess:
    def test_builds_params_from_coord(self, client: OpenSkyClient, session: Any, bbox: list[float]) -> None:
        session.get.return_value = make_response({"states": []})
        client.get_aircraft_in_bbox(bbox)
        session.get.assert_called_once_with(
            "https://opensky-network.org/api/states/all",
            params={
                "lamin": bbox[0],
                "lamax": bbox[1],
                "lomin": bbox[2],
                "lomax": bbox[3],
            },
        )

    def test_returns_states(self, client: OpenSkyClient, session: Any, bbox: list[float]) -> None:
        states = [["abc123"], ["def456"]]
        session.get.return_value = make_response({"states": states})
        result = client.get_aircraft_in_bbox(bbox)
        assert result == states

    def test_returns_empty_when_states_missing(self, client: OpenSkyClient, session: Any, bbox: list[float]) -> None:
        session.get.return_value = make_response({"time": 123})
        result = client.get_aircraft_in_bbox(bbox)
        assert result == []

    def test_returns_empty_when_states_none(self, client: OpenSkyClient, session: Any, bbox: list[float]) -> None:
        session.get.return_value = make_response({"states": None})
        result = client.get_aircraft_in_bbox(bbox)
        assert result == []

    def test_sleeps_one_second(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: Any,
        bbox: list[float],
    ) -> None:
        sleep_calls: list[float] = []
        monkeypatch.setattr("time.sleep", lambda s: sleep_calls.append(s))
        c = OpenSkyClient()
        monkeypatch.setattr(c, "session", session)
        session.get.return_value = make_response({"states": []})
        c.get_aircraft_in_bbox(bbox)

        assert sleep_calls == [1]


# ---------- get_aircraft_in_bbox: ошибки ----------


class TestGetAircraftInBboxErrors:
    def test_returns_empty_on_http_error(self, client: OpenSkyClient, session: Any, bbox: list[float]) -> None:
        session.get.return_value = make_response({}, status_ok=False)
        result = client.get_aircraft_in_bbox(bbox)
        assert result == []

    def test_returns_empty_on_connection_error(self, client: OpenSkyClient, session: Any, bbox: list[float]) -> None:
        session.get.side_effect = requests.ConnectionError("no network")
        result = client.get_aircraft_in_bbox(bbox)
        assert result == []

    def test_returns_empty_on_timeout(self, client: OpenSkyClient, session: Any, bbox: list[float]) -> None:
        session.get.side_effect = requests.Timeout("timeout")
        result = client.get_aircraft_in_bbox(bbox)
        assert result == []

    def test_returns_empty_on_any_exception(self, client: OpenSkyClient, session: Any, bbox: list[float]) -> None:
        session.get.side_effect = ValueError("something else")
        result = client.get_aircraft_in_bbox(bbox)
        assert result == []

    def test_does_not_sleep_on_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: Any,
        bbox: list[float],
    ) -> None:
        sleep_calls: list[float] = []
        monkeypatch.setattr("time.sleep", lambda s: sleep_calls.append(s))
        c = OpenSkyClient()
        monkeypatch.setattr(c, "session", session)
        session.get.side_effect = requests.ConnectionError("no network")
        c.get_aircraft_in_bbox(bbox)
        assert sleep_calls == []
