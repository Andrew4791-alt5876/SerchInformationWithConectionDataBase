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
        Получает список самолётов в прямоугольной области (bounding box).
        Возвращает сырые данные в виде списка.
        """
        if not list_of_coord_country:
            print("В запросе отсутствуют координаты страны!")
            return []
        list_of_aircraft = []
        n = 0
        for coord in list_of_coord_country:
            n += 1
            try:
                params = {"lamin": coord[0], "lamax": coord[1], "lomin": coord[2], "lomax": coord[3]}
                data = self.get_data(params=params)["states"]
                list_of_aircraft += data
                time.sleep(1)
            except BaseException:
                return []
        return list_of_aircraft
