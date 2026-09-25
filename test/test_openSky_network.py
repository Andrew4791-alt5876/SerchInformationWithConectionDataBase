from unittest.mock import MagicMock, patch

import pytest
import requests

from src.openSky_network import OpenSkyClient


@pytest.fixture
def client() -> OpenSkyClient:
    return OpenSkyClient()


# ============================================================
# get_data
# ============================================================


def test_get_data_builds_url_and_params(client):
    client.session = MagicMock()
    resp = MagicMock()
    resp.json.return_value = {"states": []}
    client.session.get.return_value = resp

    result = client.get_data(params={"lamin": 1, "lamax": 2, "lomin": 3, "lomax": 4})

    client.session.get.assert_called_once_with(
        "https://opensky-network.org/api/states/all",
        params={"lamin": 1, "lamax": 2, "lomin": 3, "lomax": 4},
    )
    resp.raise_for_status.assert_called_once()
    assert result == {"states": []}


def test_get_data_passes_none_when_params_missing(client):
    client.session = MagicMock()
    client.session.get.return_value = MagicMock(json=lambda: {})

    client.get_data()

    client.session.get.assert_called_once_with(
        "https://opensky-network.org/api/states/all",
        params=None,
    )


def test_get_data_raises_on_http_error(client):
    client.session = MagicMock()
    resp = MagicMock()
    resp.raise_for_status.side_effect = requests.HTTPError("500")
    client.session.get.return_value = resp

    with pytest.raises(requests.HTTPError):
        client.get_data()


def test_get_data_raises_on_connection_error(client):
    client.session = MagicMock()
    client.session.get.side_effect = requests.ConnectionError("boom")

    with pytest.raises(requests.ConnectionError):
        client.get_data()


# ============================================================
# get_aircraft_in_bbox — пустой вход
# ============================================================


def test_bbox_empty_coord_returns_empty_and_prints(client, capsys):
    result = client.get_aircraft_in_bbox([])

    assert result == []
    assert "отсутствуют координаты" in capsys.readouterr().out


def test_bbox_empty_coord_does_not_call_get_data(client):
    client.get_data = MagicMock()

    client.get_aircraft_in_bbox([])

    client.get_data.assert_not_called()


# ============================================================
# get_aircraft_in_bbox — успешный сценарий
# ============================================================


def test_bbox_returns_states_from_response(client):
    states = [["abc", "CALL1"], ["def", "CALL2"]]
    client.get_data = MagicMock(return_value={"states": states})

    with patch("time.sleep"):
        result = client.get_aircraft_in_bbox([10.0, 20.0, 30.0, 40.0])

    assert result == states


def test_bbox_passes_correct_params_to_get_data(client):
    client.get_data = MagicMock(return_value={"states": []})

    with patch("time.sleep"):
        client.get_aircraft_in_bbox([10.0, 20.0, 30.0, 40.0])

    client.get_data.assert_called_once_with(params={"lamin": 10.0, "lamax": 20.0, "lomin": 30.0, "lomax": 40.0})


def test_bbox_sleeps_once_after_success(client):
    client.get_data = MagicMock(return_value={"states": []})

    with patch("time.sleep") as mock_sleep:
        client.get_aircraft_in_bbox([1, 2, 3, 4])

    mock_sleep.assert_called_once_with(1)


def test_bbox_ignores_extra_elements_in_coord(client):
    """coord из 5+ элементов — лишние игнорируются (используются только [0:4])."""
    client.get_data = MagicMock(return_value={"states": []})

    with patch("time.sleep"):
        client.get_aircraft_in_bbox([1, 2, 3, 4, 5, 6])

    client.get_data.assert_called_once_with(params={"lamin": 1, "lamax": 2, "lomin": 3, "lomax": 4})


# ============================================================
# get_aircraft_in_bbox — граничные случаи ответа
# ============================================================


def test_bbox_returns_empty_when_states_key_missing(client):
    client.get_data = MagicMock(return_value={})
    with patch("time.sleep"):
        result = client.get_aircraft_in_bbox([1, 2, 3, 4])
    assert result == []


def test_bbox_returns_empty_when_states_is_none(client):
    client.get_data = MagicMock(return_value={"states": None})
    with patch("time.sleep"):
        result = client.get_aircraft_in_bbox([1, 2, 3, 4])
    assert result == []


def test_bbox_returns_empty_when_states_is_empty_list(client):
    client.get_data = MagicMock(return_value={"states": []})
    with patch("time.sleep"):
        result = client.get_aircraft_in_bbox([1, 2, 3, 4])
    assert result == []


# ============================================================
# get_aircraft_in_bbox — ошибки (текущее поведение: проглотить и вернуть [])
# ============================================================


def test_bbox_returns_empty_on_get_data_exception(client):
    client.get_data = MagicMock(side_effect=requests.ConnectionError("boom"))
    with patch("time.sleep"):
        result = client.get_aircraft_in_bbox([1, 2, 3, 4])
    assert result == []


def test_bbox_returns_empty_on_http_error(client):
    client.get_data = MagicMock(side_effect=requests.HTTPError("500"))
    with patch("time.sleep"):
        result = client.get_aircraft_in_bbox([1, 2, 3, 4])
    assert result == []


def test_bbox_returns_empty_on_short_coord(client):
    """coord из 2 элементов → IndexError внутри try → []."""
    client.get_data = MagicMock(return_value={"states": [["x"]]})
    with patch("time.sleep"):
        result = client.get_aircraft_in_bbox([1, 2])
    assert result == []


def test_bbox_does_not_sleep_on_error(client):
    client.get_data = MagicMock(side_effect=requests.ConnectionError("boom"))
    with patch("time.sleep") as mock_sleep:
        client.get_aircraft_in_bbox([1, 2, 3, 4])
    mock_sleep.assert_not_called()
