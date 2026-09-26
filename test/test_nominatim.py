from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
import requests

from src.nominatim import NominatimClient

# ---------- фикстуры ----------


@pytest.fixture
def session() -> Any:
    """Мок requests.Session. Any — чтобы mypy не проверял атрибуты мока."""
    return MagicMock()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, session: Any) -> NominatimClient:
    """Клиент с замоканной сессией и заглушённым sleep."""
    monkeypatch.setattr("time.sleep", lambda _: None)
    c = NominatimClient()
    monkeypatch.setattr(c, "session", session)
    return c


def make_response(json_data: Any, status_ok: bool = True) -> Any:
    """Фейковый requests.Response."""
    response = MagicMock()
    response.json.return_value = json_data
    if status_ok:
        response.raise_for_status.return_value = None
    else:
        response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    return response


# ---------- __init__ ----------


class TestNominatimInit:
    def test_default_endpoint(self) -> None:
        assert NominatimClient().endpoint == "/search"

    def test_custom_endpoint(self) -> None:
        assert NominatimClient(endpoint="/lookup").endpoint == "/lookup"

    def test_base_url(self) -> None:
        assert NominatimClient().base_url == "https://nominatim.openstreetmap.org"

    def test_user_agent_header_is_set(self) -> None:
        c = NominatimClient()
        assert "User-Agent" in c.headers
        assert "MyAircraftTracker" in c.headers["User-Agent"]

    def test_last_request_time_starts_at_zero(self) -> None:
        assert NominatimClient()._last_request_time == 0.0


# ---------- _rate_limit ----------


class TestRateLimit:
    def test_first_call_does_not_sleep(self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient) -> None:
        sleep_calls: list[float] = []
        monkeypatch.setattr("time.sleep", lambda s: sleep_calls.append(s))
        monkeypatch.setattr("time.time", lambda: 100.0)
        client._rate_limit()
        assert sleep_calls == []
        assert client._last_request_time == 100.0

    def test_second_call_sleeps_remaining_time(self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient) -> None:
        sleep_calls: list[float] = []
        monkeypatch.setattr("time.sleep", lambda s: sleep_calls.append(s))

        times = iter([100.0, 100.0, 100.3, 100.3])
        monkeypatch.setattr("time.time", lambda: next(times))

        client._rate_limit()  # now=100.0, last=100.0, без сна
        client._rate_limit()  # now=100.3, 0.3<1 → sleep(0.7), last=100.3

        assert sleep_calls == [pytest.approx(0.7)]

    def test_no_sleep_when_more_than_one_second_passed(
        self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient
    ) -> None:
        sleep_calls: list[float] = []
        monkeypatch.setattr("time.sleep", lambda s: sleep_calls.append(s))

        times = iter([100.0, 100.0, 102.5, 102.5])
        monkeypatch.setattr("time.time", lambda: next(times))

        client._rate_limit()  # now=100.0, last=100.0
        client._rate_limit()  # now=102.5, 2.5>1 → без сна

        assert sleep_calls == []

    def test_updates_last_request_time(self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient) -> None:
        monkeypatch.setattr("time.sleep", lambda _: None)

        times = iter([100.0, 100.0, 100.5, 101.0])
        monkeypatch.setattr("time.time", lambda: next(times))

        client._rate_limit()  # now=100.0, last=100.0
        client._rate_limit()  # now=100.5, sleep(0.5), last=101.0

        assert client._last_request_time == 101.0


# ---------- get_data ----------


class TestGetData:
    def test_calls_correct_url(self, client: NominatimClient, session: Any) -> None:
        session.get.return_value = make_response([])
        client.get_data()
        session.get.assert_called_once_with(
            "https://nominatim.openstreetmap.org/search",
            params=None,
        )

    def test_passes_params(self, client: NominatimClient, session: Any) -> None:
        session.get.return_value = make_response([])
        params = {"q": "Germany", "format": "json", "limit": 1}
        client.get_data(params=params)
        session.get.assert_called_once_with(
            "https://nominatim.openstreetmap.org/search",
            params=params,
        )

    def test_returns_json(self, client: NominatimClient, session: Any) -> None:
        payload = [{"display_name": "Germany", "boundingbox": ["47.27", "55.06", "5.87", "15.04"]}]
        session.get.return_value = make_response(payload)
        assert client.get_data() == payload

    def test_raises_for_status(self, client: NominatimClient, session: Any) -> None:
        session.get.return_value = make_response([], status_ok=False)
        with pytest.raises(requests.HTTPError):
            client.get_data()

    def test_propagates_connection_error(self, client: NominatimClient, session: Any) -> None:
        session.get.side_effect = requests.ConnectionError("no network")
        with pytest.raises(requests.ConnectionError):
            client.get_data()


# ---------- get_country_coordinates: успех ----------


class TestGetCountryCoordinatesSuccess:
    def test_returns_bbox(self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient) -> None:
        bbox = ["47.27", "55.06", "5.87", "15.04"]
        monkeypatch.setattr(
            client,
            "_make_request",
            lambda *a, **kw: [{"boundingbox": bbox}],
        )

        assert client.get_country_coordinates("Germany") == bbox

    def test_passes_search_endpoint_and_params(self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient) -> None:
        captured: dict[str, Any] = {}

        def fake(endpoint: str, params: Any, headers: Any = None) -> Any:
            captured["endpoint"] = endpoint
            captured["params"] = params
            captured["headers"] = headers
            return [{"boundingbox": ["1", "2", "3", "4"]}]

        monkeypatch.setattr(client, "_make_request", fake)

        client.get_country_coordinates("Germany")

        assert captured["endpoint"] == "search"
        assert captured["params"] == {"q": "Germany", "format": "json", "limit": 1}
        assert captured["headers"] == client.headers

    def test_takes_first_result(self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient) -> None:
        monkeypatch.setattr(
            client,
            "_make_request",
            lambda *a, **kw: [
                {"boundingbox": ["1", "2", "3", "4"]},
                {"boundingbox": ["5", "6", "7", "8"]},
            ],
        )

        assert client.get_country_coordinates("Germany") == ["1", "2", "3", "4"]


# ---------- get_country_coordinates: краевые и ошибочные ----------


class TestGetCountryCoordinatesErrors:
    def test_empty_list_returns_empty(self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient) -> None:
        monkeypatch.setattr(client, "_make_request", lambda *a, **kw: [])

        assert client.get_country_coordinates("Germany") == []

    def test_missing_boundingbox_key_returns_empty(
        self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient
    ) -> None:
        monkeypatch.setattr(client, "_make_request", lambda *a, **kw: [{"display_name": "Germany"}])

        assert client.get_country_coordinates("Germany") == []

    def test_none_boundingbox_returns_empty(self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient) -> None:
        monkeypatch.setattr(client, "_make_request", lambda *a, **kw: [{"boundingbox": None}])

        assert client.get_country_coordinates("Germany") == []

    def test_empty_boundingbox_returns_empty(self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient) -> None:
        monkeypatch.setattr(client, "_make_request", lambda *a, **kw: [{"boundingbox": []}])

        assert client.get_country_coordinates("Germany") == []

    @pytest.mark.parametrize(
        "exc",
        [ValueError("v"), IndexError("i"), TypeError("t"), KeyError("k")],
    )
    def test_handled_exceptions_return_empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
        client: NominatimClient,
        exc: BaseException,
    ) -> None:
        def boom(*a: Any, **kw: Any) -> Any:
            raise exc

        monkeypatch.setattr(client, "_make_request", boom)

        assert client.get_country_coordinates("Germany") == []

    def test_unexpected_exception_propagates(self, monkeypatch: pytest.MonkeyPatch, client: NominatimClient) -> None:
        def boom(*a: Any, **kw: Any) -> Any:
            raise RuntimeError("unexpected")

        monkeypatch.setattr(client, "_make_request", boom)

        with pytest.raises(RuntimeError):
            client.get_country_coordinates("Germany")
