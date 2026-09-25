import json
from typing import Any

import pytest

from src import database_utils as db


class FakeCursor:
    def __init__(self, fetchone_results: Any=None) -> None:
        self.executed = []
        self._fetchone_results = list(fetchone_results or [])
        self.closed = False

    def execute(self, query: Any, params: Any=None) -> None:
        self.executed.append((query, params))

    def fetchone(self) -> None:
        if self._fetchone_results:
            return self._fetchone_results.pop(0)
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any):
        self.closed = True
        return False


class FakeConnection:
    def __init__(self, cursor) -> None:
        self._cursor = cursor
        self.committed = False
        self.closed = False

    def cursor(self) -> None:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True
        return False


class FakeDB:
    def __init__(self) -> None:
        self.connections = []
        self.fetchone_results = []

    def connect(self, **kwargs):
        cursor = FakeCursor(fetchone_results=self.fetchone_results)
        conn = FakeConnection(cursor)
        self.connections.append(conn)
        return conn


@pytest.fixture
def fake_db(monkeypatch):
    fake = FakeDB()
    monkeypatch.setattr(db.psycopg2, "connect", fake.connect)
    return fake


def write_json(tmp_path, data):
    path = tmp_path / "aircraft.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


PLANE = {
    "id_aircraft": "abc123",
    "callsign": "TEST123",
    "country": "Russia",
    "latitude": 55.0,
    "longitude": 37.0,
    "vertical_rate": 0.0,
    "velocity": 200.0,
    "altitude": 10000.0,
    "true_track": 90.0,
    "squawk": "1234",
    "on_ground": False,
}


def test_create_tables(fake_db):
    db.create_tables()

    assert len(fake_db.connections) == 1
    conn = fake_db.connections[0]
    cur = conn._cursor
    queries = [q for q, _ in cur.executed]

    assert any("DROP TABLE IF EXISTS countries, aircraft CASCADE" in q for q in queries)
    assert any("CREATE TABLE IF NOT EXISTS countries" in q for q in queries)
    assert any("CREATE TABLE IF NOT EXISTS aircraft" in q for q in queries)
    assert conn.committed is True
    assert cur.closed is True
    assert conn.closed is True


def test_insert_data_when_country_exists(fake_db, tmp_path):
    fake_db.fetchone_results = [(1,)]  # SELECT id_country -> страна найдена
    file_path = write_json(tmp_path, [PLANE])

    db.insert_data_to_db(file_path, ["Russia"])

    cur = fake_db.connections[0]._cursor
    assert len(cur.executed) == 2

    select_query, select_params = cur.executed[0]
    assert "SELECT id_country FROM countries" in select_query
    assert select_params == ("Russia",)

    insert_query, insert_params = cur.executed[1]
    assert "INSERT INTO aircraft" in insert_query
    assert insert_params == (
        "abc123",
        "TEST123",
        "Russia",
        55.0,
        37.0,
        0.0,
        200.0,
        10000.0,
        90.0,
        "1234",
        False,
        1,
    )


def test_insert_data_when_country_not_exists(fake_db, tmp_path):
    fake_db.fetchone_results = [None, (2,)]  # SELECT -> нет, INSERT countries -> id=2
    file_path = write_json(tmp_path, [PLANE])

    db.insert_data_to_db(file_path, ["Russia"])

    cur = fake_db.connections[0]._cursor
    assert len(cur.executed) == 3

    assert "SELECT id_country FROM countries" in cur.executed[0][0]
    assert cur.executed[0][1] == ("Russia",)

    assert "INSERT INTO countries" in cur.executed[1][0]
    assert cur.executed[1][1] == ("Russia",)

    assert "INSERT INTO aircraft" in cur.executed[2][0]
    assert cur.executed[2][1][-1] == 2  # country_id


def test_insert_data_empty_countries(fake_db, tmp_path):
    file_path = write_json(tmp_path, [PLANE])

    db.insert_data_to_db(file_path, [])

    cur = fake_db.connections[0]._cursor
    assert cur.executed == []


@pytest.mark.xfail(reason="Текущая реализация дублирует самолёты для каждой страны")
def test_insert_data_does_not_duplicate_aircraft_for_each_country(fake_db, tmp_path):
    fake_db.fetchone_results = [(1,), (2,)]
    file_path = write_json(tmp_path, [PLANE])

    db.insert_data_to_db(file_path, ["Russia", "USA"])

    cur = fake_db.connections[0]._cursor
    aircraft_inserts = [e for e in cur.executed if "INSERT INTO aircraft" in e[0]]
    assert len(aircraft_inserts) == 1  # ожидаем один самолёт, но сейчас будет 2
