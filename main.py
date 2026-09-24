from datetime import datetime
from typing import Any

from data_countries import list_countries
from database_utils import create_tables, insert_data_to_db
from json_saver import JSONSaver
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
        user_input = input("Введите название страны: ")
        if user_input == "0":
            break
        if user_input.isalpha() or user_input in (
            "Russian Federation",
            "United Kingdom",
            "United States",
            "Viet Nam",
            "Republic of Moldova",
            "Dominican Republic",
            "Kingdom of the Netherlands",
            "Republic of Korea",
            "Saudi Arabia",
            "Trinidad and Tobago",
            "South Africa",
            "Brunei Darussalam",
            "San Marino",
            "United Arab Emirates",
            "New Zealand",
            "Libyan Arab Jamahiriya",
            "Saint Vincent and the Grenadines",
            "Czech Republic",
            "Lao People's Democratic Republic",
            "Sri Lanka",
        ):
            print(f"Вы ввели {user_input}")
            country_user.append(user_input)
        else:
            print("Вы ввели не название страны, попробуйте еще раз!")
    return country_user


def sort_aircraft_by_altitude(list_aircraft: list, sort_altitude: Any) -> list:
    """Функция сортировки самолетов по высоте полета по убыванию или возрастанию, по желанию пользователя"""
    if sort_altitude == "y":
        sort_reverse = False
    else:
        sort_reverse = True
    sorted_planes = sorted(
        list_aircraft,
        key=lambda x: x.geo_altitude if x.geo_altitude is not None else float("inf"),
        reverse=sort_reverse,
    )
    return sorted_planes


def filter_aeroplanes_by_country(aeroplanes: list, filter_words: list) -> list:
    """Функция для сортировки самолетов по стране регистрации"""
    filtered = [plane for plane in aeroplanes if plane.origin_country in filter_words]
    return filtered


def filter_aeroplanes_altitude(aeroplanes: list) -> list:
    """Функция для сортировки самолетов по диапазону высот по желанию пользователя"""
    # Запрашиваем диапазон высот (например, "1000-5000" или "1000 5000")
    range_input = input("Введите диапазон высот полета (нижняя-верхняя через дефис или пробел): ")
    # Разбиваем ввод по дефису или пробелу
    if "-" in range_input:
        parts = range_input.split("-")
    else:
        parts = range_input.split()
    # Проверяем, что получили два значения
    if len(parts) == 2:
        try:
            low_alt = float(parts[0].strip())
            high_alt = float(parts[1].strip())
            altitude_range = [low_alt, high_alt]  # кортеж или список [low, high]
        except ValueError:
            print("Некорректный ввод. Используйте числа.")
            altitude_range = [0.0, 20000]
    else:
        print("Некорректный ввод. Нужно ввести два числа через дефис или пробел.")
        altitude_range = [0.0, 20000]
    filtered = [plane for plane in aeroplanes if altitude_range[0] <= plane.geo_altitude <= altitude_range[1]]
    return filtered


def number_of_top() -> int:
    """Функция ввода пользователем количества самолетов для вывода в консоль"""
    numb_user = input("Введите количество самолетов для вывода в топ N: ")
    if numb_user.isdigit():
        numb = int(numb_user)
    else:
        numb = 3
    return numb

def user_interaction() -> list:
    """Главная функция для запуска проекта"""
    print(f"{hello_by_current_time()}")
    print(
        "Добро пожаловать в программу, которая собирает данные о самолетах\n"
        "в воздушных пространствах тех стран, которые вы выберете.\n"
        "Пример стран из списка:"
    )
    countries = list_countries()
    user_country = country_for_coord(countries)
    user_country_correct = [
        c
        for c in user_country
        if c.lower()
        not in ("russia", "rossia", "russya", "rossya", "rusiya", "ru", "rus", "rusia", "rusland", "rwasha")
    ]
    coord = NominatimClient().get_country_coordinates(user_country_correct)
    if user_country != user_country_correct:
        coord += [["41.1833333", "81.85", "19.6333333", "180.0"], ["41.1833333", "81.85", "-180.0", "-168.9833333"]]
    # [['41.1833333', '81.85', '19.6333333', '180.0'], ['41.1833333', '81.85', '-180.0', '-168.9833333']] Russia
    # aircrafts = OpenSkyClient().get_aircraft_in_bbox(coord)
    # # for aicraft in aircrafts:
    # #     print(aicraft)
    # # print(len(aircrafts))
    # print(f"Над {user_country} находится {len(aircrafts)} самолетов.")
    # if len(aircrafts) == 0:
    #     print("Проверьте соединение с интернетом и запустите программу!")
    # list_class_aircraft = []
    # for i in aircrafts:
    #     try:
    #         plane = Aircraft(i[0], i[1], i[2], i[5], i[6], i[11], i[9], i[13], i[10], i[14], i[8], i[7])
    #         list_class_aircraft.append(plane)
    #     except Exception as e:
    #         print(f"Не удалось создать объект под номером {i}: {e}")
    #
    timestamp = datetime.now().strftime("%Y%m%d")
    file_root = f"data/aircraft_{timestamp}.json"
    # json_storage = JSONSaver(file_root)
    # planes_dicts = [plane.to_dict() for plane in list_class_aircraft]
    # json_storage._save_data(planes_dicts)
    create_tables()
    insert_data_to_db(file_root, user_country)
    # sort_altitude = input("Вам необходима сортировка самолетов от минимальной высоты и выше?: y/n ").lower()
    # n = number_of_top()
    # sorted_aircraft = sort_aircraft_by_altitude(list_class_aircraft, sort_altitude)
    # data_planes = sorted_aircraft
    return []

    # for aircraft in sorted_aircraft[:n]:
    #     print(aircraft)
    # print("*" * 150)
    # unique_countries_tuple = tuple({plane.origin_country for plane in sorted_aircraft})
    # print("Для сортировки самолетов по стране регистрации скопируйте страну из списка: ")
    # for c in range(0, len(unique_countries_tuple), 9):
    #     print(unique_countries_tuple[c: (9 + c)])
    # filter_words = country_for_coord([])
    # filtered_aeroplanes = filter_aeroplanes_by_country(sorted_aircraft, filter_words)
    # print(f"Получилось {len(filtered_aeroplanes)} самолетов по стране регистрации")
    # n = number_of_top()
    # for i in filtered_aeroplanes[:n]:
    #     print(i)
    # print("*" * 150)
    # filtered_aeroplanes_alt = filter_aeroplanes_altitude(sorted_aircraft)
    # print(f"Получилось {len(filtered_aeroplanes_alt)} самолетов в диапазоне выбранных высот")
    # n = number_of_top()
    # for r in filtered_aeroplanes_alt[:n]:
    #     print(r)
    # print("*" * 150)
    # choose_user_data = int(
    #     input(
    #         "Для сохранения данных в файл сделайте введите соответствующий пункт:\n"
    #         "    1) Сохранить базу данных всех самолетов находящихся в пределах выбранных стран\n"
    #         "    2) Сохранить базу данных самолетов, выбранных по стране регистрации\n"
    #         "    3) Сохранить базу данных самолетов, выбранных по диапазону высот\n"
    #         "    4) Ничего не сохранять (можно ничего не вводить)\n"
    #         "Сделайте свой выбор: "
    #     )
    # )
    # if choose_user_data == 1:
    #     data_planes = sorted_aircraft
    # elif choose_user_data == 2:
    #     data_planes = filtered_aeroplanes
    # elif choose_user_data == 3:
    #     data_planes = filtered_aeroplanes_alt
    # else:
    #     data_planes = []
    # return data_planes

if __name__ == "__main__":
    user_interaction()
#     timestamp = datetime.now().strftime("%Y%m%d")
#     json_storage = JSONSaver(f"data/aircraft_{timestamp}.json")
#     planes_dicts = [plane.to_dict() for plane in planes]
#     json_storage._save_data(planes_dicts)
# #     main()
# from get_aircraft import get_country_coordinates, get_aircraft_in_area
#
#
# def main():
#     list_co = get_country_coordinates(["USA"])
#     list_air = get_aircraft_in_area(list_co)
#     for r in list_air:
#         print(r)
#
# if __name__ == "__main__":
#     main()