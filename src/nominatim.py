import time
from typing import Any, Optional, cast

from src.base_api import APIClient


class NominatimClient(APIClient):
    """
    Клиент для Nominatim API (OpenStreetMap).
    Используется для получения географических координат стран.
    """

    def __init__(self, endpoint: str = "/search") -> None:
        super().__init__("https://nominatim.openstreetmap.org", endpoint=endpoint)
        self.headers = {"User-Agent": "MyAircraftTracker/1.0 (tyrandr@list.ru)"}
        self._last_request_time: float = 0.0

    def _rate_limit(self) -> None:
        now = time.time()
        if now - self._last_request_time < 1:
            time.sleep(1 - (now - self._last_request_time))
        self._last_request_time = time.time()

    def get_data(self, params: Optional[dict[Any, Any]] = None) -> dict[Any, Any]:
        url = f"{self.base_url}{self.endpoint}"  # предполагаем, что endpoint задан в __init__
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return cast(dict[Any, Any], response.json())

    def get_country_coordinates(self, country_name: list) -> list:
        list_of_coord = []
        for country in country_name:
            try:
                params = {"q": country, "format": "json", "limit": 1}
                data = self._make_request("search", params, headers=self.headers)
                coord_of_country = data[0]["boundingbox"]
                list_of_coord.append(coord_of_country)
                return list_of_coord
            except (ValueError, IndexError, TypeError, KeyError):
                return []
        return list_of_coord
