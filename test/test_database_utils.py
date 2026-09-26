from __future__ import annotations

from types import TracebackType
from typing import Any, Literal

import psycopg2
import pytest

from src.database_utils import create_tables, insert_data_to_db

# ---------- фейковые объекты psycopg2 ----------


class FakeCursor:
    """Минимальный двойник psycopg2-курсора."""

    def __init__(self, container: "FakeDB") -> None:
        self._container = container
        self.executed: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

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

    def fetchone(self) -> Any:
        results = self._container.fetchone_results
        return results.pop(0) if results else None

    def fetchall(self) -> list[Any]:
        results = self._container.fetchall_results
        self._container.fetchall_results = []
        return results


class FakeConnection:
    """Минимальный двойник psycopg2-соединения."""

    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor
        self.committed = False
        self.closed = False

    def cursor(self) -> FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        # psycopg2 коммитит при выходе из with, если не было исключения
        if exc_type is None:
            self.commit()
        self.closed = True
        return False


class FakeDB:
    """Контейнер, куда складываются все созданные соединения."""

    def __init__(self) -> None:
        self.connections: list[FakeConnection] = []
        self.fetchone_results: list[Any] = []
        self.fetchall_results: list[Any] = []


@pytest.fixture
def fake_db(monkeypatch: pytest.MonkeyPatch) -> FakeDB:
    """Подменяет psycopg2.connect на фабрику FakeConnection."""
    fake = FakeDB()

    def fake_connect(**kwargs: Any) -> FakeConnection:
        cursor = FakeCursor(fake)
        conn = FakeConnection(cursor)
        fake.connections.append(conn)
        return conn

    monkeypatch.setattr(psycopg2, "connect", fake_connect)
    return fake


# ---------- вспомогательные данные ----------


def make_plane(
    aircraft_id: str = "abc123",
    callsign: str = "TEST123",
    country: str = "Germany",
    latitude: float = 52.5,
    longitude: float = 13.4,
) -> dict[str, Any]:
    return {
        "id_aircraft": aircraft_id,
        "callsign": callsign,
        "country": country,
        "latitude": latitude,
        "longitude": longitude,
        "vertical_rate": 0.0,
        "velocity": 200.0,
        "altitude": 10000.0,
        "true_track": 90.0,
        "squawk": "1234",
        "on_ground": False,
    }


# ---------- create_tables ----------


def test_create_tables_opens_one_connection(fake_db: FakeDB) -> None:
    create_tables()
    assert len(fake_db.connections) == 1


def test_create_tables_executes_drop_and_both_creates(fake_db: FakeDB) -> None:
    create_tables()
    cur = fake_db.connections[0]._cursor
    queries = [q for q, _ in cur.executed]

    assert any("DROP TABLE IF EXISTS countries, aircraft CASCADE" in q for q in queries)
    assert any("CREATE TABLE IF NOT EXISTS countries" in q for q in queries)
    assert any("CREATE TABLE IF NOT EXISTS aircraft" in q for q in queries)


def test_create_tables_countries_columns(fake_db: FakeDB) -> None:
    create_tables()
    cur = fake_db.connections[0]._cursor
    sql = next(q for q, _ in cur.executed if "CREATE TABLE IF NOT EXISTS countries" in q)
    assert "id_country SERIAL PRIMARY KEY" in sql
    assert "name_country VARCHAR(100) NOT NULL" in sql


def test_create_tables_aircraft_columns(fake_db: FakeDB) -> None:
    create_tables()
    cur = fake_db.connections[0]._cursor
    sql = next(q for q, _ in cur.executed if "CREATE TABLE IF NOT EXISTS aircraft" in q)
    for column in (
        "id",
        "aircraft_id",
        "callsign",
        "origin_country",
        "latitude",
        "longitude",
        "vertical_rate",
        "velocity",
        "altitude",
        "true_track",
        "squawk",
        "on_ground",
        "country_id",
    ):
        assert column in sql
    assert "REFERENCES countries" in sql
    assert "ON DELETE CASCADE" in sql


def test_create_tables_commits_and_closes(fake_db: FakeDB) -> None:
    create_tables()
    conn = fake_db.connections[0]
    assert conn.committed is True
    assert conn.closed is True
    assert conn._cursor.closed is True


def test_create_tables_prints_success(fake_db: FakeDB, capsys: pytest.CaptureFixture[str]) -> None:
    create_tables()
    out = capsys.readouterr().out
    assert "Таблицы успешно созданы!" in out


# ---------- insert_data_to_db: страна уже есть ----------


def test_insert_country_exists_uses_existing_id(fake_db: FakeDB) -> None:
    fake_db.fetchone_results = [(7,)]  # SELECT id_country -> найдено
    planes = [make_plane()]

    insert_data_to_db(planes, "Germany")

    cur = fake_db.connections[0]._cursor
    assert len(cur.executed) == 2  # 1 SELECT + 1 INSERT aircraft

    select_query, select_params = cur.executed[0]
    assert "SELECT id_country FROM countries" in select_query
    assert select_params == ("Germany",)

    insert_query, insert_params = cur.executed[1]
    assert "INSERT INTO aircraft" in insert_query
    assert insert_params[0] == "abc123"
    assert insert_params[1] == "TEST123"
    assert insert_params[2] == "Germany"
    assert insert_params[-1] == 7


def test_insert_country_exists_does_not_create_country(fake_db: FakeDB) -> None:
    fake_db.fetchone_results = [(7,)]
    insert_data_to_db([make_plane()], "Germany")

    cur = fake_db.connections[0]._cursor
    assert not any("INSERT INTO countries" in q for q, _ in cur.executed)


# ---------- insert_data_to_db: страны ещё нет ----------


def test_insert_country_not_exists_creates_it(fake_db: FakeDB) -> None:
    fake_db.fetchone_results = [None, (3,)]  # SELECT -> нет, INSERT RETURNING -> 3
    planes = [make_plane()]

    insert_data_to_db(planes, "Germany")

    cur = fake_db.connections[0]._cursor
    assert len(cur.executed) == 3

    assert "SELECT id_country FROM countries" in cur.executed[0][0]
    assert cur.executed[0][1] == ("Germany",)

    assert "INSERT INTO countries" in cur.executed[1][0]
    assert cur.executed[1][1] == ("Germany",)

    insert_query, insert_params = cur.executed[2]
    assert "INSERT INTO aircraft" in insert_query
    assert insert_params[-1] == 3


def test_insert_country_not_exists_uses_returning(fake_db: FakeDB) -> None:
    fake_db.fetchone_results = [None, (42,)]
    insert_data_to_db([make_plane()], "Germany")

    cur = fake_db.connections[0]._cursor
    country_insert = next(q for q, _ in cur.executed if "INSERT INTO countries" in q)
    assert "RETURNING id_country" in country_insert


# ---------- один country_id для всех самолётов ----------


def test_all_planes_get_same_country_id(fake_db: FakeDB) -> None:
    fake_db.fetchone_results = [(5,)]
    planes = [
        make_plane(aircraft_id="a1"),
        make_plane(aircraft_id="a2"),
        make_plane(aircraft_id="a3"),
    ]

    insert_data_to_db(planes, "Germany")

    cur = fake_db.connections[0]._cursor
    aircraft_inserts = [e for e in cur.executed if "INSERT INTO aircraft" in e[0]]
    assert len(aircraft_inserts) == 3

    country_ids = [params[-1] for _, params in aircraft_inserts]
    assert country_ids == [5, 5, 5]


# ---------- пустой список самолётов ----------


def test_empty_aircraft_list_does_not_insert_aircraft(fake_db: FakeDB) -> None:
    fake_db.fetchone_results = [(1,)]

    insert_data_to_db([], "Germany")

    cur = fake_db.connections[0]._cursor
    aircraft_inserts = [e for e in cur.executed if "INSERT INTO aircraft" in e[0]]
    assert aircraft_inserts == []


def test_empty_planes_still_inserts_country(fake_db: FakeDB) -> None:
    fake_db.fetchone_results = [None, (9,)]  # страны нет -> создаётся

    insert_data_to_db([], "Germany")

    cur = fake_db.connections[0]._cursor
    queries = [q for q, _ in cur.executed]
    assert any("SELECT id_country FROM countries" in q for q in queries)
    assert any("INSERT INTO countries" in q for q in queries)
    assert not any("INSERT INTO aircraft" in q for q in queries)


# ---------- порядок параметров ----------


def test_insert_params_order_matches_columns(fake_db: FakeDB) -> None:
    fake_db.fetchone_results = [(1,)]
    plane = make_plane(
        aircraft_id="ID1",
        callsign="CALL1",
        country="France",
        latitude=48.85,
        longitude=2.35,
    )

    insert_data_to_db([plane], "France")

    cur = fake_db.connections[0]._cursor
    _, params = next(e for e in cur.executed if "INSERT INTO aircraft" in e[0])
    assert params == (
        "ID1",
        "CALL1",
        "France",
        48.85,
        2.35,
        0.0,
        200.0,
        10000.0,
        90.0,
        "1234",
        False,
        1,
    )


# ---------- коммит и печать ----------


def test_insert_commits_and_closes(fake_db: FakeDB) -> None:
    fake_db.fetchone_results = [(1,)]
    insert_data_to_db([make_plane()], "Germany")

    conn = fake_db.connections[0]
    assert conn.committed is True
    assert conn.closed is True
    assert conn._cursor.closed is True


def test_insert_prints_success(fake_db: FakeDB, capsys: pytest.CaptureFixture[str]) -> None:
    fake_db.fetchone_results = [(1,)]
    insert_data_to_db([make_plane()], "Germany")

    out = capsys.readouterr().out
    assert "Germany" in out
    assert "успешно загружены" in out
