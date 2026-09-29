from __future__ import annotations

import os
from types import TracebackType
from typing import Any, Literal
from unittest.mock import MagicMock

import psycopg2
import pytest

from src import manadger
from src.manadger import DBManager

# env vars нужны, чтобы src.database_utils.conn_params импортировался
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_pass")


# ---------- фейковые psycopg2 ----------


class FakeCursor:
    """Минимальный двойник psycopg2-курсора."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.executed: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False
        self.cursor_factory: Any = None

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        self.closed = True
        return False

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        self.executed.append((query, params))

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows

    def fetchone(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None


class FakeConnection:
    """Минимальный двойник psycopg2-соединения."""

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows: list[dict[str, Any]] = rows or []
        self.cursors: list[FakeCursor] = []
        self.closed = False

    def cursor(self, cursor_factory: Any = None) -> FakeCursor:
        cur = FakeCursor(self.rows)
        cur.cursor_factory = cursor_factory
        self.cursors.append(cur)
        return cur

    def close(self) -> None:
        self.closed = True

    def commit(self) -> None:
        pass


# ---------- фикстуры ----------


@pytest.fixture
def fake_conn() -> FakeConnection:
    return FakeConnection()


@pytest.fixture
def manager(monkeypatch: pytest.MonkeyPatch, fake_conn: FakeConnection) -> DBManager:
    """DBManager с замоканным psycopg2.connect."""
    monkeypatch.setattr(psycopg2, "connect", lambda **kwargs: fake_conn)
    return DBManager(params={"dbname": "test"})


def last_cursor(fake_conn: FakeConnection) -> FakeCursor:
    """Курсор, созданный последним вызовом _fetchall."""
    return fake_conn.cursors[-1]


# ---------- __init__ ----------


class TestInit:
    def test_passes_params_to_connect(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, Any] = {}

        def fake_connect(**kwargs: Any) -> MagicMock:
            captured.update(kwargs)
            return MagicMock()

        monkeypatch.setattr(psycopg2, "connect", fake_connect)

        DBManager(params={"dbname": "x", "user": "y", "password": "z"})

        assert captured == {"dbname": "x", "user": "y", "password": "z"}

    def test_uses_default_conn_params_when_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, Any] = {}

        def fake_connect(**kwargs: Any) -> MagicMock:
            captured.update(kwargs)
            return MagicMock()

        monkeypatch.setattr(psycopg2, "connect", fake_connect)

        DBManager()  # params=None → берётся conn_params

        assert captured == manadger.conn_params

    def test_stores_connection(self, monkeypatch: pytest.MonkeyPatch, fake_conn: FakeConnection) -> None:
        monkeypatch.setattr(psycopg2, "connect", lambda **kwargs: fake_conn)
        m = DBManager(params={"dbname": "test"})
        assert m._conn is fake_conn


# ---------- _fetchall ----------


class TestFetchall:
    def test_executes_query_with_params(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        fake_conn.rows = [{"x": 1}]

        result = manager._fetchall("SELECT %s", ("a",))

        assert result == [{"x": 1}]
        query, params = last_cursor(fake_conn).executed[0]
        assert query == "SELECT %s"
        assert params == ("a",)

    def test_default_params_is_empty_tuple(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager._fetchall("SELECT 1")
        _, params = last_cursor(fake_conn).executed[0]
        assert params == ()

    def test_uses_real_dict_cursor(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        from psycopg2.extras import RealDictCursor

        manager._fetchall("SELECT 1")

        assert last_cursor(fake_conn).cursor_factory is RealDictCursor

    def test_cursor_is_closed_after_use(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager._fetchall("SELECT 1")
        assert last_cursor(fake_conn).closed is True

    def test_returns_fetchall_result(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        fake_conn.rows = [{"a": 1}, {"a": 2}]
        assert manager._fetchall("SELECT a") == [{"a": 1}, {"a": 2}]


# ---------- get_countries_and_aeroplanes_count ----------


class TestGetCountriesAndAeroplanesCount:
    def test_query_contains_join_group_by_order_by(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager.get_countries_and_aeroplanes_count()
        query, _ = last_cursor(fake_conn).executed[0]
        assert "COUNT(a.id)" in query
        assert "LEFT JOIN aircraft" in query
        assert "GROUP BY c.name_country" in query
        assert "ORDER BY" in query

    def test_returns_rows(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        fake_conn.rows = [
            {"country": "Germany", "aeroplanes_count": 5},
            {"country": "France", "aeroplanes_count": 3},
        ]
        result = manager.get_countries_and_aeroplanes_count()
        assert result == [
            {"country": "Germany", "aeroplanes_count": 5},
            {"country": "France", "aeroplanes_count": 3},
        ]


# ---------- get_all_aeroplanes ----------


class TestGetAllAeroplanes:
    def test_query_contains_join_and_order(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager.get_all_aeroplanes()
        query, _ = last_cursor(fake_conn).executed[0]
        assert "FROM aircraft a" in query
        assert "LEFT JOIN countries c" in query
        assert "ORDER BY a.id" in query

    def test_selects_all_columns(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager.get_all_aeroplanes()
        query, _ = last_cursor(fake_conn).executed[0]
        for column in (
            "a.id",
            "a.aircraft_id",
            "a.callsign",
            "a.origin_country",
            "a.latitude",
            "a.longitude",
            "a.vertical_rate",
            "a.velocity",
            "a.altitude",
            "a.true_track",
            "a.squawk",
            "a.on_ground",
        ):
            assert column in query
        assert "c.name_country AS country" in query

    def test_returns_rows(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        fake_conn.rows = [{"id": 1, "callsign": "ABC"}]
        assert manager.get_all_aeroplanes() == [{"id": 1, "callsign": "ABC"}]


# ---------- get_avg_speed ----------


class TestGetAvgSpeed:
    def test_returns_value(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        fake_conn.rows = [{"avg_speed": 250.5}]
        assert manager.get_avg_speed() == 250.5

    def test_returns_none_when_no_rows(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        fake_conn.rows = []
        assert manager.get_avg_speed() is None

    def test_returns_none_when_avg_is_null(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        # пустая таблица или все velocity = NULL → AVG вернёт NULL
        fake_conn.rows = [{"avg_speed": None}]
        assert manager.get_avg_speed() is None

    def test_query_is_avg_velocity(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager.get_avg_speed()
        query, _ = last_cursor(fake_conn).executed[0]
        assert "AVG(velocity)" in query
        assert "FROM aircraft" in query


# ---------- get_aeroplanes_with_higher_speed ----------


class TestGetAeroplanesWithHigherSpeed:
    def test_query_uses_subquery_avg(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager.get_aeroplanes_with_higher_speed()
        query, _ = last_cursor(fake_conn).executed[0]
        assert "AVG(velocity)" in query
        assert "velocity >" in query

    def test_query_orders_desc(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager.get_aeroplanes_with_higher_speed()
        query, _ = last_cursor(fake_conn).executed[0]
        assert "ORDER BY velocity DESC" in query

    def test_selects_callsign_and_velocity(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager.get_aeroplanes_with_higher_speed()
        query, _ = last_cursor(fake_conn).executed[0]
        assert "callsign" in query
        assert "velocity" in query

    def test_returns_rows(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        fake_conn.rows = [
            {"callsign": "FAST1", "velocity": 500.0},
            {"callsign": "FAST2", "velocity": 400.0},
        ]
        assert manager.get_aeroplanes_with_higher_speed() == [
            {"callsign": "FAST1", "velocity": 500.0},
            {"callsign": "FAST2", "velocity": 400.0},
        ]


# ---------- get_aeroplanes_with_keyword ----------


class TestGetAeroplanesWithKeyword:
    def test_query_uses_like(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager.get_aeroplanes_with_keyword("ABC")
        query, _ = last_cursor(fake_conn).executed[0]
        assert "LIKE" in query
        assert "callsign" in query

    def test_wraps_keyword_in_percent(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager.get_aeroplanes_with_keyword("ABC")
        _, params = last_cursor(fake_conn).executed[0]
        assert params == ("%ABC%",)

    def test_empty_keyword(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        manager.get_aeroplanes_with_keyword("")
        _, params = last_cursor(fake_conn).executed[0]
        assert params == ("%%",)

    def test_keyword_with_percent_is_not_escaped(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        # символ % внутри keyword остаётся wildcard'ом — фиксируем текущее поведение
        manager.get_aeroplanes_with_keyword("A%B")
        _, params = last_cursor(fake_conn).executed[0]
        assert params == ("%A%B%",)

    def test_returns_rows(self, manager: DBManager, fake_conn: FakeConnection) -> None:
        fake_conn.rows = [{"callsign": "ABC123"}]
        assert manager.get_aeroplanes_with_keyword("ABC") == [{"callsign": "ABC123"}]
