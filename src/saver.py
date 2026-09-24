from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.aircrafts import Aircraft


class Saver(ABC):
    """Абстрактный базовый класс для всех хранилищ данных о самолётах."""

    @abstractmethod
    def add_aircraft(self, aircraft: Aircraft) -> None:
        """
        Добавляет информацию о самолёте в хранилище.
        :param aircraft: Объект Aircraft
        """
        pass

    @abstractmethod
    def get_aircraft(self, criteria: Optional[Dict[str, Any]] = None) -> List[Aircraft]:
        """
        Возвращает список самолётов, удовлетворяющих критериям.
        Если criteria == None, возвращает все записи.
        Критерии задаются словарём вида {поле: значение}. Проверяется точное совпадение.
        :param criteria: Словарь с условиями фильтрации
        :return: список объектов Aircraft
        """
        pass

    @abstractmethod
    def delete_aircraft(self, criteria: Optional[Dict[str, Any]] = None) -> None:
        """
        Удаляет записи о самолётах, удовлетворяющих критериям.
        Если criteria == None, удаляет все записи.
        :param criteria: Словарь с условиями фильтрации
        """
        pass
