import time
from typing import Any, Optional, cast

from src.base_api import APIClient


class OpenSkyClient(APIClient):
    """
    Клиент для OpenSky Network API.
    Используется для получения информации о самолётах в заданном регионе.
    """

    def __init__(self, endpoint: str = "/states/all") -> None:
        super().__init__(base_url="https://opensky-network.org/api", endpoint=endpoint)

    def get_data(self, params: Optional[dict[Any, Any]] = None) -> dict[Any, Any]:
        url = f"{self.base_url}{self.endpoint}"
        response = self.session.get(url, params=params)  # <-- здесь создаётся response
        response.raise_for_status()
        return cast(dict[Any, Any], response.json())

    def get_aircraft_in_bbox(self, coord: list) -> list:
        """Получает самолёты для каждого bounding box из списка."""
        if not coord:
            print("В запросе отсутствуют координаты страны!")
            return []
        all_aircraft: list = []
        try:
            params = {"lamin": coord[0], "lamax": coord[1], "lomin": coord[2], "lomax": coord[3]}
            response = self.get_data(params=params)
            states = response.get("states") or []
            all_aircraft.extend(states)
            time.sleep(1)
        except Exception:
            return []
        return all_aircraft
