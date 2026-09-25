import os
from dotenv import load_dotenv
import psycopg2


load_dotenv()
conn_params = {
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "host": "localhost",
    "port": 5432,
    "client_encoding": "UTF8",
}


def create_tables() -> None:
    """Создает таблицы в базе данных"""
    with psycopg2.connect(**conn_params) as conn:  # type: ignore[call-overload]
        with conn.cursor() as cur:
            cur.execute("""
                DROP TABLE IF EXISTS countries, aircraft CASCADE
                """)
            cur.execute("""CREATE TABLE IF NOT EXISTS countries(id_country SERIAL PRIMARY KEY,
            name_country VARCHAR(100) NOT NULL);""")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS aircraft(
                id SERIAL PRIMARY KEY, aircraft_id VARCHAR(50) NOT NULL,
                callsign VARCHAR(50) NOT NULL,origin_country VARCHAR(100),
                latitude FLOAT,longitude FLOAT,vertical_rate FLOAT,
                velocity FLOAT,altitude FLOAT,true_track FLOAT,
                squawk VARCHAR(10),on_ground BOOLEAN,
                country_id INTEGER REFERENCES countries (id_country) ON DELETE CASCADE
                );
                """)
        conn.commit()
    print("Таблицы успешно созданы!")

def insert_data_to_db(dict_of_aircraft: list[dict], country: str) -> None:
    """Записывает страну и все её самолёты в БД."""
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_country FROM countries WHERE name_country = %s;",
                (country,),
            )
            result = cur.fetchone()
            if result:
                country_id = result[0]
            else:
                cur.execute(
                    "INSERT INTO countries (name_country) VALUES (%s) "
                    "RETURNING id_country;",
                    (country,),
                )
                country_id = cur.fetchone()[0]

            for plane in dict_of_aircraft:
                cur.execute(
                    """
                    INSERT INTO aircraft (
                        aircraft_id, callsign, origin_country,
                        latitude, longitude, vertical_rate,
                        velocity, altitude, true_track,
                        squawk, on_ground, country_id
                    ) VALUES (%s, %s, %s, %s, %s, %s,
                              %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        plane["id_aircraft"],
                        plane["callsign"],
                        plane["country"],
                        plane["latitude"],
                        plane["longitude"],
                        plane["vertical_rate"],
                        plane["velocity"],
                        plane["altitude"],
                        plane["true_track"],
                        plane["squawk"],
                        plane["on_ground"],
                        country_id,
                    ),
                )
    print(f"Самолёты страны {country!r} успешно загружены!")
