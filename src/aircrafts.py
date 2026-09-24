from typing import Any, Optional


class Aircraft:
    def __init__(
        self,
        id_aircraft: str,
        callsign: str,
        origin_country: str,
        longitude: Optional[float] = None,
        latitude: Optional[float] = None,
        vertical_rate: Optional[float] = None,
        velocity: Optional[float] = None,
        geo_altitude: Optional[float] = None,
        true_track: Optional[float] = None,
        squawk: Optional[str] = None,
        on_ground: Optional[bool] = None,
        bar_altitude: Optional[float] = None,
    ) -> None:
        # Строковые поля
        self.id_aircraft = id_aircraft if isinstance(id_aircraft, str) else ""
        self.callsign = callsign.strip() if isinstance(callsign, str) else ""
        self.origin_country = origin_country if isinstance(origin_country, str) else ""

        # Координаты
        self.longitude = float(longitude) if isinstance(longitude, (int, float)) and -180 <= longitude <= 180 else 0.0
        self.latitude = float(latitude) if isinstance(latitude, (int, float)) and -90 <= latitude <= 90 else 0.0

        # Высоты (барометрическая и геометрическая)
        self.bar_altitude = (
            float(bar_altitude) if isinstance(bar_altitude, (int, float)) and bar_altitude >= 0 else 0.0
        )
        self.geo_altitude = (
            float(geo_altitude) if isinstance(geo_altitude, (int, float)) and geo_altitude >= 0 else self.bar_altitude
        )

        # Состояние на земле
        self.on_ground = bool(on_ground) if on_ground is not None else False

        # Скорость и курс
        self.velocity = float(velocity) if isinstance(velocity, (int, float)) else 0.0
        self.true_track = float(true_track) if isinstance(true_track, (int, float)) and 0 <= true_track <= 360 else 0.0

        # Вертикальная скорость
        self.vertical_rate = float(vertical_rate) if isinstance(vertical_rate, (int, float)) else 0.0

        # Код squawk
        self.squawk = squawk if isinstance(squawk, str) else "2000"

    def __repr__(self) -> str:
        """Строковое представление объекта для отладки."""
        return (
            f"Aircraft(id_aircraft='{self.id_aircraft}', callsign='{self.callsign}', country='{self.origin_country}', "
            f"lat={self.latitude}, lon={self.longitude}, vert_rate={self.vertical_rate}, "
            f"vel={self.velocity}, alt={self.geo_altitude}, "
            f"true_track={self.true_track}, squawk='{self.squawk}', on_ground={self.on_ground})"
        )

    def __eq__(self, other: Any) -> bool:
        """Сравнение на равенство по скорости и высоте."""
        if not isinstance(other, Aircraft):
            return NotImplemented
        return (self.velocity, self.geo_altitude) == (other.velocity, other.geo_altitude)

    def __lt__(self, other: Any) -> bool:
        """Сравнение 'меньше' по скорости и высоте."""
        if not isinstance(other, Aircraft):
            return NotImplemented
        return (self.velocity, self.geo_altitude) < (other.velocity, other.geo_altitude)

    def to_dict(self) -> dict:
        """Преобразует объект в словарь для сохранения в JSON."""
        return {
            "id_aircraft": self.id_aircraft,
            "callsign": self.callsign,
            "country": self.origin_country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "vertical_rate": self.vertical_rate,
            "velocity": self.velocity,
            "altitude": self.geo_altitude,
            "true_track": self.true_track,
            "squawk": self.squawk,
            "on_ground": self.on_ground,
            "bar_altitude": self.bar_altitude,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Aircraft":
        """Создаёт объект Aircraft из словаря."""
        return cls(
            id_aircraft=data.get("id_aircraft", ""),
            callsign=data.get("callsign", ""),
            origin_country=data.get("country", ""),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            vertical_rate=data.get("vertical_rate"),
            velocity=data.get("velocity"),
            geo_altitude=data.get("altitude"),
            true_track=data.get("true_track"),
            squawk=data.get("squawk"),
            on_ground=data.get("on_ground"),
            bar_altitude=data.get("bar_altitude"),
        )
