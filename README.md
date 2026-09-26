# SerchInformationWithConectionDataBase

Консольное приложение для сбора и анализа данных о самолётах в воздушном пространстве выбранных стран.

Программа получает координаты стран через **Nominatim (OpenStreetMap)**, 
запрашивает данные о самолётах через **OpenSky Network API**, 
сохраняет их в **PostgreSQL** и выводит статистику.

---

## Возможности

- Приветствие в зависимости от времени суток.
- Выбор одной или нескольких стран из списка (ввод в консоли).
- Получение ограничивающего прямоугольника (bounding box) страны через Nominatim.
- Запрос списка самолётов, находящихся в этом прямоугольнике, через OpenSky Network.
- Преобразование «сырых» данных OpenSky в объекты `Aircraft` с валидацией полей.
- Сохранение стран и самолётов в PostgreSQL.
- Отчёты по базе:
  - количество самолётов по странам;
  - первые 10 самолётов с позывными, страной регистрации, скоростью и высотой;
  - средняя скорость по всем самолётам;
  - самолёты, летящие быстрее средней скорости;
  - самолёты с заданной подстрокой в позывном.

---

## Стек

- Python 3.13
- PostgreSQL
- [`requests`](https://pypi.org/project/requests/) — HTTP-запросы к API
- [`psycopg2`](https://pypi.org/project/psycopg2/) — драйвер PostgreSQL
- [`python-dotenv`](https://pypi.org/project/python-dotenv/) — переменные окружения
- [`pytest`](https://pypi.org/project/pytest/) — тесты
- [`mypy`](https://pypi.org/project/mypy/) — статическая типизация
- [`flake8`](https://pypi.org/project/flake8/) / 
- [`black`](https://pypi.org/project/black/) / 
- [`isort`](https://pypi.org/project/isort/) — линтеры и форматирование

---

## Структура проекта

```
SerchInformationWithConectionDataBase/

├── src/
│   ├── __init__.py
│   ├── aircrafts.py         # модель Aircraft
│   ├── base_api.py          # базовый класс APIClient
│   ├── database_utils.py
│   ├── manadger.py          # класс DBManager — запросы к БД
│   ├── nominatim.py         # клиент Nominatim
│   └── openSky_network.py   # клиент OpenSky Network
├── test/
│   ├── conftest.py          # общие фикстуры
│   ├── test_aircrafts.py
│   ├── test_base_api.py
│   ├── test_database_utils.py
│   ├── test_nominatim.py
│   └── test_openSky_network.py
├── pyproject.toml           # зависимости и конфиги (poetry, mypy, pytest, black, isort)
├── .env                     # секреты (не коммитится)
├── .env.example             # шаблон переменных окружения
├── data_countries.py        # список доступных стран
├── main.py                  # точка входа, сценарий работы программы
└── README.md
```

---

## Установка

### 1. Клонировать репозиторий

```bash
git clone <url>
cd SerchInformationWithConectionDataBase
```

### 2. Создать виртуальное окружение

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate   # Linux / macOS
```

### 3. Установить зависимости

Через Poetry:

```bash
poetry install
```

Или через pip:

```bash
pip install -e .
pip install -r requirements.txt   # если есть
```

### 4. Настроить подключение к PostgreSQL

Создайте файл `.env` в корне проекта:

```env
DB_NAME=aircraft_db
DB_USER=postgres
DB_PASSWORD=your_password
```

Параметры `host` и `port` зашиты в `database_utils.py` (`localhost:5432`), при необходимости поправьте их там или вынесите в `.env`.

### 5. Создать базу данных

```bash
psql -U postgres -c "CREATE DATABASE aircraft_db;"
```

Таблицы создаются автоматически при первом запуске — функция `create_tables()`.

---

## Использование

Запустите:

```bash
python main.py
```

Программа попросит выбрать страны. Введите название страны **точно как в списке** (список печатается порциями по 9), для завершения ввода — `0`.

Пример сессии:

```
Добрый день!
Добро пожаловать в программу, которая собирает данные о самолетах
в воздушных пространствах тех стран, которые вы выберете.
Пример стран из списка:
['Germany', 'France', 'Italy', 'Spain', ...]
Для прекращения ввода введите цифру 0
Введите название страны из образца стран: Germany
Вы ввели Germany
Введите название страны из образца стран: 0

Над Germany находится 42 самолетов.

Страны и количество самолётов:
  Germany: 42

Вывод первых 10 самолетов
    1  DLH123    Germany               250.5   10500.0  Germany
    ...

Средняя скорость: 231.7

Самолёты быстрее среднего:
  DLH456: 312.4
  ...

С ключевыми символами 'A'в позывном :
  DLH123
  ...
```

---

## База данных

### Схема

**`countries`**

| Колонка | Тип | Описание |
|---|---|---|
| `id_country` | `SERIAL PRIMARY KEY` | ID страны |
| `name_country` | `VARCHAR(100) NOT NULL` | Название |

**`aircraft`**

| Колонка | Тип | Описание |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | ID записи |
| `aircraft_id` | `VARCHAR(50) NOT NULL` | ICAO24 |
| `callsign` | `VARCHAR(50) NOT NULL` | Позывной |
| `origin_country` | `VARCHAR(100)` | Страна регистрации |
| `latitude` | `FLOAT` | Широта |
| `longitude` | `FLOAT` | Долгота |
| `vertical_rate` | `FLOAT` | Вертикальная скорость |
| `velocity` | `FLOAT` | Скорость |
| `altitude` | `FLOAT` | Высота |
| `true_track` | `FLOAT` | Курс |
| `squawk` | `VARCHAR(10)` | Код squawk |
| `on_ground` | `BOOLEAN` | На земле |
| `country_id` | `INTEGER REFERENCES countries(id_country) ON DELETE CASCADE` | Страна |

### Запросы через `DBManager`

```python
from manadger import DBManager

manager = DBManager()

manager.get_countries_and_aeroplanes_count()   # стран + количество самолётов
manager.get_all_aeroplanes()                    # все самолёты
manager.get_avg_speed()                         # средняя скорость
manager.get_aeroplanes_with_higher_speed()      # быстрее среднего
manager.get_aeroplanes_with_keyword("A")        # по подстроке в позывном
```

Все методы возвращают `list[dict[str, Any]]` (благодаря `RealDictCursor`), поэтому к полям обращаются по именам: `row["callsign"]`, `row["velocity"]`.

---

## Тесты

Запуск всех тестов:

```bash
pytest
```

Только конкретный файл:

```bash
pytest test/test_aircrafts.py -v
```

С покрытием:

```bash
pytest --cov=src --cov=.
```

Тесты используют `monkeypatch` и `MagicMock`, реальные запросы в сеть и БД не выполняются.

---

## Линтеры и типы

```bash
mypy src test
flake8 src test
black src test
isort src test
```

Конфигурация — в `pyproject.toml`:
- mypy: strict (`disallow_untyped_defs = true`), исключая `.venv`;
- black / isort: длина строки 119;
- pytest: `pythonpath = [".", "src"]`.

---

## Известные особенности

- **Nominatim** ограничивает частоту запросов до 1 в секунду. В `NominatimClient._rate_limit()` реализована задержка через `time.sleep`, поэтому тесты обязаны глушить `time.sleep` через `monkeypatch`.
- **OpenSky Network** также имеет лимиты на анонимные запросы. В `OpenSkyClient.get_aircraft_in_bbox()` после каждого запроса стоит `time.sleep(1)`.
- Поля `bar_altitude` и `geo_altitude` — необязательные. Если `geo_altitude` отсутствует или отрицательный, используется `bar_altitude`.
- `squawk` в БД хранится как строка, потому что в API это строка из 4 цифр, иногда с ведущими нулями.
- **Опечатки в именах файлов.** `manadger.py` (вместо `manager.py`) и `openSky_network.py` (вместо `opensky_network.py` / `open_sky_network.py`) — стоит поправить при рефакторинге.

---

## Лицензия

Учебный проект. Используйте свободно.
