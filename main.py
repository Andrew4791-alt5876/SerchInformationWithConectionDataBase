from datetime import datetime
from data_countries import list_countries
from database_utils import create_tables, insert_data_to_db
from manadger import DBManager
from src.aircrafts import Aircraft
from src.nominatim import NominatimClient
from src.openSky_network import OpenSkyClient


def hello_by_current_time() -> str:
    """Функция, которая формирует приветственное сообщение в зависимости от фактического времени суток."""
    now_hour = datetime.now().hour
    if 6 <= now_hour < 12:
        hello_message = "Доброе утро!"
    elif 12 <= now_hour < 18:
        hello_message = "Добрый день!"
    elif 18 <= now_hour <= 23:
        hello_message = "Добрый вечер!"
    else:
        hello_message = "Доброй ночи!"
    return hello_message


def country_for_coord(countries: list) -> list:
    """Функция для ввода стран пользователем"""
    for i in range(0, len(countries), 9):
        print(countries[i: (9 + i)])
    country_user = []
    while True:
        print("Для прекращения ввода введите цифру 0")
        user_input = input("Введите название страны из образца стран: ")
        if user_input == "0":
            break
        elif user_input.isalpha() and user_input in (countries):
            print(f"Вы ввели {user_input}")
            country_user.append(user_input)
        else:
            print("Вы ввели не название страны, попробуйте еще раз!")
    return country_user


def main():
    """Главная функция для запуска проекта"""
    print(f"{hello_by_current_time()}")
    # print(
    #     "Добро пожаловать в программу, которая собирает данные о самолетах\n"
    #     "в воздушных пространствах тех стран, которые вы выберете.\n"
    #     "Пример стран из списка:"
    # )
    # user_country = country_for_coord(list_countries())
    # create_tables()
    # for country in user_country:
    #     coord = NominatimClient().get_country_coordinates(country)
    #     aircrafts = OpenSkyClient().get_aircraft_in_bbox(coord)
    #     if len(aircrafts) == 0:
    #         print("Проверьте соединение с интернетом и запустите программу!")
    #     else:
    #         print(f"Над {country} находится {len(aircrafts)} самолетов.")
    #     list_class_aircraft = []
    #     for i in aircrafts:
    #         try:
    #             plane = Aircraft(i[0], i[1], i[2], i[5], i[6], i[11], i[9], i[13], i[10], i[14], i[8], i[7])
    #             list_class_aircraft.append(plane)
    #         except Exception as e:
    #             print(f"Не удалось создать объект под номером {i}: {e}")
    #     planes_dicts = [plane.to_dict() for plane in list_class_aircraft]
    #     insert_data_to_db(planes_dicts, country)
    manager = DBManager()
    print("\nСтраны и количество самолётов:")
    for row in manager.get_countries_and_aeroplanes_count():
        print(f'  {row["country"]}: {row["aeroplanes_count"]}')

    print("\nВывод первых 10 самолетов")
    for row in manager.get_all_aeroplanes()[:10]:
        print(
            f"{row['id']:>5}  "
            f"{row['callsign'] or '—':<10}  "
            f"{row['origin_country'] or '—':<20}  "
            f"{row['velocity'] if row['velocity'] is not None else '—':>6}  "
            f"{row['altitude'] if row['altitude'] is not None else '—':>7}  "
            f"{row['country'] or '—'}"
        )

    print(f'\nСредняя скорость: {manager.get_avg_speed()}')

    print("\nСамолёты быстрее среднего:")
    for row in manager.get_aeroplanes_with_higher_speed()[:10]:
        print(f'  {row["callsign"]}: {row["velocity"]}')

    print("\nС ключевыми символами 'A'в позывном :")
    for row in manager.get_aeroplanes_with_keyword("A")[:10]:
        print(f'  {row["callsign"]}')


if __name__ == "__main__":
    main()
