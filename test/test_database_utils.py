import pytest

import database_utils as db

# ---------- фейковые объекты psycopg2 ----------


class FakeCursor:
    def __init__(self, fetchone_results=None):
        self.executed: list[tuple] = []
        self._fetchone_results = list(fetchone_results or [])
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self._fetchone_results.pop(0) if self._fetchone_results else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True
        return False


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True
        return False


class FakeDB:
    def __init__(self):
        self.connections: list[FakeConnection] = []
        self.fetchone_results = []

    def connect(self, **kwargs):
        cursor = FakeCursor(self.fetchone_results)
        conn = FakeConnection(cursor)
        self.connections.append(conn)
        return conn


@pytest.fixture
def fake_db(monkeypatch):
    fake = FakeDB()
    monkeypatch.setattr(db.psycopg2, "connect", fake.connect)
    return fake


# ---------- тестовые данные ----------


def make_plane(
    aircraft_id="abc123",
    callsign="TEST123",
    country="Germany",
    latitude=52.5,
    longitude=13.4,
):
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


def test_create_tables_executes_drop_and_create(fake_db):
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


def test_create_tables_countries_has_columns(fake_db):
    db.create_tables()
    cur = fake_db.connections[0]._cursor
    countries_sql = next(q for q, _ in cur.executed if "CREATE TABLE IF NOT EXISTS countries" in q)

    assert "id_country SERIAL PRIMARY KEY" in countries_sql
    assert "name_country VARCHAR(100) NOT NULL" in countries_sql


def test_create_tables_aircraft_has_columns(fake_db):
    db.create_tables()
    cur = fake_db.connections[0]._cursor
    aircraft_sql = next(q for q, _ in cur.executed if "CREATE TABLE IF NOT EXISTS aircraft" in q)

    for column in (
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
        assert column in aircraft_sql

    assert "REFERENCES countries" in aircraft_sql
    assert "ON DELETE CASCADE" in aircraft_sql


# ---------- insert_data_to_db: страна уже есть ----------


def test_insert_country_exists_uses_existing_id(fake_db):
    fake_db.fetchone_results = [(7,)]  # SELECT id_country -> найдено
    planes = [make_plane()]

    db.insert_data_to_db(planes, "Germany")

    cur = fake_db.connections[0]._cursor
    # 1 SELECT + 1 INSERT на самолёт
    assert len(cur.executed) == 2

    select_query, select_params = cur.executed[0]
    assert "SELECT id_country FROM countries" in select_query
    assert select_params == ("Germany",)

    insert_query, insert_params = cur.executed[1]
    assert "INSERT INTO aircraft" in insert_query
    # последний параметр — country_id
    assert insert_params[-1] == 7
    assert insert_params[0] == "abc123"
    assert insert_params[1] == "TEST123"
    assert insert_params[2] == "Germany"


# ---------- insert_data_to_db: страны ещё нет ----------


def test_insert_country_not_exists_creates_it(fake_db):
    fake_db.fetchone_results = [None, (3,)]  # SELECT -> нет, INSERT -> id=3
    planes = [make_plane()]

    db.insert_data_to_db(planes, "Germany")

    cur = fake_db.connections[0]._cursor
    assert len(cur.executed) == 3

    assert "SELECT id_country FROM countries" in cur.executed[0][0]
    assert cur.executed[0][1] == ("Germany",)

    assert "INSERT INTO countries" in cur.executed[1][0]
    assert cur.executed[1][1] == ("Germany",)

    insert_query, insert_params = cur.executed[2]
    assert "INSERT INTO aircraft" in insert_query
    assert insert_params[-1] == 3


# ---------- один country_id для всех самолётов ----------


def test_all_planes_get_same_country_id(fake_db):
    fake_db.fetchone_results = [(5,)]
    planes = [
        make_plane(aircraft_id="a1"),
        make_plane(aircraft_id="a2"),
        make_plane(aircraft_id="a3"),
    ]

    db.insert_data_to_db(planes, "Germany")

    cur = fake_db.connections[0]._cursor
    aircraft_inserts = [e for e in cur.executed if "INSERT INTO aircraft" in e[0]]
    assert len(aircraft_inserts) == 3

    country_ids = [params[-1] for _, params in aircraft_inserts]
    assert country_ids == [5, 5, 5]


# ---------- самолётов нет ----------


def test_empty_aircraft_list_does_not_insert_aircraft(fake_db):
    fake_db.fetchone_results = [(1,)]

    db.insert_data_to_db([], "Germany")

    cur = fake_db.connections[0]._cursor
    aircraft_inserts = [e for e in cur.executed if "INSERT INTO aircraft" in e[0]]
    assert aircraft_inserts == []


# ---------- пустой список стран/самолётов: страна всё равно заводится ----------


def test_empty_planes_still_inserts_country(fake_db):
    fake_db.fetchone_results = [None, (9,)]  # страны нет -> создаётся

    db.insert_data_to_db([], "Germany")

    cur = fake_db.connections[0]._cursor
    queries = [q for q, _ in cur.executed]
    assert any("SELECT id_country FROM countries" in q for q in queries)
    assert any("INSERT INTO countries" in q for q in queries)
    assert not any("INSERT INTO aircraft" in q for q in queries)


# ---------- порядок параметров совпадает с колонками ----------


def test_insert_params_order_matches_columns(fake_db):
    fake_db.fetchone_results = [(1,)]
    plane = make_plane(
        aircraft_id="ID1",
        callsign="CALL1",
        country="France",
        latitude=48.85,
        longitude=2.35,
    )

    db.insert_data_to_db([plane], "France")

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
