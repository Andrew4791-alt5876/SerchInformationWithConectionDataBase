import json
from typing import Any, Dict, List, Optional, cast

from src.aircrafts import Aircraft
from src.saver import Saver


class JSONSaver(Saver):
    """Реализация хранилища на основе JSON-файла."""

    # Маппинг атрибутов Aircraft на ключи в JSON
    _ATTR_TO_JSON = {
        "id_aircraft": "id_aircraft",
        "callsign": "callsign",
        "origin_country": "country",
        "longitude": "longitude",
        "latitude": "latitude",
        "vertical_rate": "vertical_rate",
        "velocity": "velocity",
        "geo_altitude": "altitude",
        "true_track": "true_track",
        "squawk": "squawk",
        "on_ground": "on_ground",
        "bar_altitude": "bar_altitude",
    }

    def __init__(self, filename: str):
        self.filename = filename

    def _load_data(self) -> List[Dict[str, Any]]:
        """Загружает данные из JSON-файла. Если файла нет, возвращает пустой список."""
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cast(list[dict[str, Any]], data)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_data(self, data: List[Dict[str, Any]]) -> None:
        """Сохраняет данные в JSON-файл."""
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_aircraft(self, aircraft: Aircraft) -> None:
        data = self._load_data()
        data.append(aircraft.to_dict())
        self._save_data(data)

    def get_aircraft(self, criteria: Optional[Dict[str, Any]] = None) -> List[Aircraft]:
        data = self._load_data()
        if criteria is None:
            return [Aircraft.from_dict(item) for item in data]
        filtered = []
        for item in data:
            match = True
            for attr, value in criteria.items():
                if attr in self._ATTR_TO_JSON:
                    json_key = self._ATTR_TO_JSON[attr]
                    if item.get(json_key) != value:
                        match = False
                        break
                else:
                    # Неизвестный атрибут – условие не выполняется
                    match = False
                    break
            if match:
                filtered.append(Aircraft.from_dict(item))
        return filtered

    def delete_aircraft(self, criteria: Optional[Dict[str, Any]] = None) -> None:
        data = self._load_data()
        if criteria is None:
            self._save_data([])
            return

        new_data = []
        for item in data:
            keep = True
            for attr, value in criteria.items():
                if attr in self._ATTR_TO_JSON:
                    json_key = self._ATTR_TO_JSON[attr]
                    if item.get(json_key) == value:
                        # Если хотя бы одно условие совпало, запись удаляется
                        keep = False
                        break
                else:
                    # Неизвестный атрибут – не удаляем такую запись
                    keep = True
                    break
            if keep:
                new_data.append(item)
        self._save_data(new_data)
