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

    def get_aircraft_in_bbox(self, list_of_coord_country: list) -> list:
        """
        Получает список самолётов в прямоугольных областях (bounding box)
        для каждой страны из списка.
        """
        if not list_of_coord_country:
            return []
        all_aircraft: list = []
        try:
            lamin, lamax, lomin, lomax = (float(value) for value in list_of_coord_country[:4])
            params = {
                "lamin": lamin,
                "lamax": lamax,
                "lomin": lomin,
                "lomax": lomax,
            }
            response = self.get_data(params=params)
            states = response.get("states") or []
            all_aircraft.extend(states)
            time.sleep(1)  # уважаем rate limit OpenSky
        except (ValueError, TypeError, KeyError, IndexError) as error:
            return error
        return all_aircraft
