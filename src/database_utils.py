import json
import psycopg2

conn_params = {
    "dbname": "aircraft",
    "user": "postgres",
    "password": "A12345!",
    "host": "localhost",
    "port": 5432,
    "client_encoding": "UTF8"
}


def create_tables():
    """Создает таблицы в базе данных"""
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DROP TABLE IF EXISTS countries, aircraft CASCADE
                """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS countries (
                id_country SERIAL PRIMARY KEY, 
                name_country VARCHAR(100) NOT NULL
                );
                """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS aircraft (
                id SERIAL PRIMARY KEY,
                aircraft_id VARCHAR(50) NOT NULL,
                callsign VARCHAR(50) NOT NULL,
                origin_country VARCHAR(100),
                latitude FLOAT,
                longitude FLOAT,
                vertical_rate FLOAT,
                velocity FLOAT,
                altitude FLOAT,
                true_track FLOAT,
                skuawk VARCHAR(10),
                on_ground BOOLEAN,
                country_id INTEGER REFERENCES 
                countries (id_country) ON DELETE CASCADE
                );
                """)
        conn.commit()
    print("Таблицы успешно созданы!")


def insert_data_to_db(file_root, list_countries):
    """Читает JSON и заполняет таблицы данными."""
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            with open(file_root, "r", encoding="utf-8") as file:
                dict_of_response = json.load(file)
                for country in list_countries:
                    cur.execute("""SELECT id_country FROM countries
                     WHERE name_country = %s;""", (country,))
                    result = cur.fetchone()
                    if result:
                        country_id = result[0]
                    else:
                        cur.execute(
                            """
                            INSERT INTO countries (name_country) VALUES (%s)
                            RETURNING id_country;""", (country,)
                        )
                        country_id = cur.fetchone()[0]
                    for plane in dict_of_response:
                        cur.execute("""INSERT INTO aircraft (
                        aircraft_id, callsign, origin_country, latitude, longitude, 
                        vertical_rate, velocity, altitude, true_track,
                        skuawk, on_ground, country_id) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        );""", (
                            plane["id_aircraft"], plane["callsign"],
                            plane["country"], plane["latitude"],
                            plane["longitude"], plane["vertical_rate"],
                            plane["velocity"], plane["altitude"],
                            plane["true_track"], plane["squawk"],
                            plane["on_ground"], country_id
                        ))
    print("Данные успешно загружены в базу данных!")

# if __name__ == "__main__":
#     create_tables()