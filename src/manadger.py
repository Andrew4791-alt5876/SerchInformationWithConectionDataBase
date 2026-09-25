from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from database_utils import conn_params


class DBManager:
    """Работа с данными о странах и самолётах в БД PostgreSQL."""

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self._params = params or conn_params

    def _fetchall(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        with psycopg2.connect(**self._params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()

    def get_countries_and_aeroplanes_count(self) -> list[dict[str, Any]]:
        """Список всех стран и количество самолётов в их воздушном пространстве."""
        return self._fetchall("""
            SELECT c.name_country AS country,
                   COUNT(a.id)    AS aeroplanes_count
            FROM countries c
            LEFT JOIN aircraft a ON a.country_id = c.id_country
            GROUP BY c.name_country
            ORDER BY aeroplanes_count DESC, country;
        """)

    def get_all_aeroplanes(self) -> list[dict[str, Any]]:
        """Список всех воздушных судов."""
        return self._fetchall("""
            SELECT a.id,
                   a.aircraft_id,
                   a.callsign,
                   a.origin_country,
                   a.latitude,
                   a.longitude,
                   a.vertical_rate,
                   a.velocity,
                   a.altitude,
                   a.true_track,
                   a.squawk,
                   a.on_ground,
                   c.name_country AS country
            FROM aircraft a
            LEFT JOIN countries c ON c.id_country = a.country_id
            ORDER BY a.id;
        """)

    def get_avg_speed(self) -> float | None:
        """Средняя скорость по всем самолётам."""
        rows = self._fetchall("""
            SELECT AVG(velocity) AS avg_speed
            FROM aircraft
            WHERE velocity IS NOT NULL;
        """)
        return rows[0]["avg_speed"] if rows else None

    def get_aeroplanes_with_higher_speed(self) -> list[dict[str, Any]]:
        """Самолёты, скорость которых выше средней."""
        return self._fetchall("""
            SELECT a.id,
                   a.aircraft_id,
                   a.callsign,
                   a.origin_country,
                   a.velocity,
                   a.altitude,
                   a.on_ground,
                   c.name_country AS country
            FROM aircraft a
            LEFT JOIN countries c ON c.id_country = a.country_id
            WHERE a.velocity > (
                SELECT AVG(velocity) FROM aircraft WHERE velocity IS NOT NULL
            )
            ORDER BY a.velocity DESC;
        """)

    def get_aeroplanes_with_keyword(self, keyword: str) -> list[dict[str, Any]]:
        """Самолёты, в позывном которых содержится подстрока keyword."""
        return self._fetchall("""
            SELECT a.id,
                   a.aircraft_id,
                   a.callsign,
                   a.origin_country,
                   a.velocity,
                   a.altitude,
                   a.on_ground,
                   c.name_country AS country
            FROM aircraft a
            LEFT JOIN countries c ON c.id_country = a.country_id
            WHERE a.callsign ILIKE %s
            ORDER BY a.callsign;
        """, (f"%{keyword}%",))
