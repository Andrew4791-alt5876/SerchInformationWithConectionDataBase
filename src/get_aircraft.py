# import requests
# import time
#
#
# def get_country_coordinates(country_name: list) -> list:
#     list_of_coord = []
#     url = "https://nominatim.openstreetmap.org/search"
#     headers = {"User-Agent": "FlightTrackerCoursework/1.0 (tyrandr@list.ru)"}
#     for country in country_name:
#         try:
#             params = {"q": country, "format": "json", "limit": 1}
#             response = requests.get(url, headers=headers, params=params)
#             if response.status_code == 200:
#                 data = response.json()
#                 coord_of_country = data[0]["boundingbox"]
#                 list_of_coord.append(coord_of_country)
#         except (ValueError, IndexError, TypeError, KeyError):
#             return []
#     return list_of_coord
#
#
# def get_aircraft_in_area(list_of_coord_country: list) -> list:
#     url = "https://opensky-network.org/api/states/all"
#     if not list_of_coord_country:
#         print("В запросе отсутствуют координаты страны!")
#         return []
#     list_of_aircraft = []
#     for coord in list_of_coord_country:
#         try:
#             params = {"lamin": coord[0], "lamax": coord[1], "lomin": coord[2], "lomax": coord[3]}
#             response = requests.get(url, params=params)
#             if response.status_code == 200:
#                 data = response.json()
#                 states = data.get("states", [])
#                 if states:
#                     for i in states:
#                         i[11] = i[11] if i[11] else 0
#                         i[13] = i[13] if i[13] else 0
#                         i[7] = i[7] if i[7] else 0
#                         i[14] = i[14] if i[14] else '2000'
#                         aircraft = [i[0], i[1], i[2], i[5], i[6], i[11],i[9], i[13], i[10], i[14], i[8], i[7]]
#                         list_of_aircraft.append(aircraft)
#                         time.sleep(1)
#         except BaseException:
#             continue
#     return list_of_aircraft


# if __name__ == "__main__":
#     # [['-14.7608358', '71.5889534', '-180.0000000', '180.0000000'],
#     #  ['41.6765597', '83.3362128', '-141.0027500', '-52.3237664']]
#     list_co = get_country_coordinates(["USA"])
#     list_air = get_aircraft_in_area(list_co)
#     for r in list_air:
#         print(r)