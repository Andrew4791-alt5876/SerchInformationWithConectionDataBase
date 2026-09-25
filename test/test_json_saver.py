import json
from pathlib import Path

import pytest

from src.aircrafts import Aircraft
from src.json_saver import JSONSaver


class TestJSONSaver:
    """Тесты для JSONSaver."""

    @pytest.fixture
    def sample_aircraft(self) -> Aircraft:
        return Aircraft(
            id_aircraft="ABC123",
            callsign="ABC123",
            origin_country="Russia",
            longitude=55.0,
            latitude=37.0,
            vertical_rate=10.5,
            velocity=250.3,
            geo_altitude=10000.0,
            true_track=180.0,
            squawk="1234",
            on_ground=False,
            bar_altitude=9500.0,
        )

    @pytest.fixture
    def sample_aircraft_2(self) -> Aircraft:
        return Aircraft(
            id_aircraft="DEF456",
            callsign="DEF456",
            origin_country="USA",
            longitude=-80.0,
            latitude=40.0,
            vertical_rate=5.0,
            velocity=300.0,
            geo_altitude=12000.0,
            true_track=90.0,
            squawk="5678",
            on_ground=True,
            bar_altitude=11500.0,
        )

    @pytest.fixture
    def sample_aircraft_3(self) -> Aircraft:
        return Aircraft(
            id_aircraft="GHI789",
            callsign="GHI789",
            origin_country="Russia",
            longitude=60.0,
            latitude=55.0,
            vertical_rate=8.0,
            velocity=280.0,
            geo_altitude=11000.0,
            true_track=270.0,
            squawk="9012",
            on_ground=False,
            bar_altitude=10500.0,
        )

    def test_init(self, tmp_path: Path) -> None:
        """Проверка инициализации с именем файла."""
        filename = tmp_path / "test.json"
        saver = JSONSaver(str(filename))
        assert saver.filename == str(filename)

    def test_load_data_file_not_exists(self, tmp_path: Path) -> None:
        """При отсутствии файла _load_data возвращает пустой список."""
        filename = tmp_path / "nonexistent.json"
        saver = JSONSaver(str(filename))
        data = saver._load_data()
        assert data == []

    def test_load_data_corrupted_json(self, tmp_path: Path) -> None:
        """При повреждённом JSON возвращается пустой список."""
        filename = tmp_path / "corrupt.json"
        filename.write_text("this is not json", encoding="utf-8")
        saver = JSONSaver(str(filename))
        data = saver._load_data()
        assert data == []

    def test_save_data_creates_file(self, tmp_path: Path) -> None:
        """_save_data создаёт файл с корректным JSON."""
        filename = tmp_path / "test.json"
        saver = JSONSaver(str(filename))
        test_data = [{"key": "value"}]
        saver._save_data(test_data)

        assert filename.exists()
        with open(filename, "r", encoding="utf-8") as f:
            content = json.load(f)
        assert content == test_data

    def test_add_aircraft(self, tmp_path: Path, sample_aircraft: Aircraft) -> None:
        """add_aircraft добавляет самолёт в файл."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)

        data = saver._load_data()
        assert len(data) == 1
        assert data[0]["id_aircraft"] == "ABC123"

    def test_get_aircraft_all(self, tmp_path: Path, sample_aircraft: Aircraft, sample_aircraft_2: Aircraft) -> None:
        """get_aircraft без критериев возвращает все самолёты."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)
        saver.add_aircraft(sample_aircraft_2)

        all_aircraft = saver.get_aircraft()
        assert len(all_aircraft) == 2
        assert all_aircraft[0].id_aircraft == "ABC123"
        assert all_aircraft[1].id_aircraft == "DEF456"

    def test_get_aircraft_with_criteria_single(
        self, tmp_path: Path, sample_aircraft: Aircraft, sample_aircraft_2: Aircraft, sample_aircraft_3: Aircraft
    ) -> None:
        """get_aircraft с одним критерием фильтрации."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)
        saver.add_aircraft(sample_aircraft_2)
        saver.add_aircraft(sample_aircraft_3)

        # Фильтр по стране
        result = saver.get_aircraft({"origin_country": "Russia"})
        assert len(result) == 2
        assert set(a.id_aircraft for a in result) == {"ABC123", "GHI789"}

        # Фильтр по on_ground
        result = saver.get_aircraft({"on_ground": True})
        assert len(result) == 1
        assert result[0].id_aircraft == "DEF456"

    def test_get_aircraft_with_criteria_multiple(
        self, tmp_path: Path, sample_aircraft: Aircraft, sample_aircraft_2: Aircraft, sample_aircraft_3: Aircraft
    ) -> None:
        """get_aircraft с несколькими критериями (AND)."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)
        saver.add_aircraft(sample_aircraft_2)
        saver.add_aircraft(sample_aircraft_3)

        # Страна = Russia и on_ground = False
        result = saver.get_aircraft({"origin_country": "Russia", "on_ground": False})
        assert len(result) == 2
        assert set(a.id_aircraft for a in result) == {"ABC123", "GHI789"}

        # Страна = Russia и velocity = 250.3
        result = saver.get_aircraft({"origin_country": "Russia", "velocity": 250.3})
        assert len(result) == 1
        assert result[0].id_aircraft == "ABC123"

    def test_get_aircraft_no_match(self, tmp_path: Path, sample_aircraft: Aircraft) -> None:
        """get_aircraft с критериями, не дающими совпадений."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)

        result = saver.get_aircraft({"origin_country": "France"})
        assert result == []

        result = saver.get_aircraft({"non_existent_field": "value"})
        assert result == []

    def test_delete_all_aircraft(self, tmp_path: Path, sample_aircraft: Aircraft, sample_aircraft_2: Aircraft) -> None:
        """delete_aircraft без критериев удаляет все записи."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)
        saver.add_aircraft(sample_aircraft_2)

        saver.delete_aircraft()
        assert saver.get_aircraft() == []

    def test_delete_aircraft_by_criteria_single(
        self, tmp_path: Path, sample_aircraft: Aircraft, sample_aircraft_2: Aircraft, sample_aircraft_3: Aircraft
    ) -> None:
        """delete_aircraft с одним критерием удаляет подходящие записи."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)
        saver.add_aircraft(sample_aircraft_2)
        saver.add_aircraft(sample_aircraft_3)

        # Удаляем все с on_ground = True
        saver.delete_aircraft({"on_ground": True})
        remaining = saver.get_aircraft()
        assert len(remaining) == 2
        assert set(a.id_aircraft for a in remaining) == {"ABC123", "GHI789"}

    def test_delete_aircraft_by_criteria_multiple(
        self, tmp_path: Path, sample_aircraft: Aircraft, sample_aircraft_2: Aircraft, sample_aircraft_3: Aircraft
    ) -> None:
        """delete_aircraft с несколькими критериями удаляет только записи, удовлетворяющие всем."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)
        saver.add_aircraft(sample_aircraft_2)
        saver.add_aircraft(sample_aircraft_3)

        # Удаляем Russia с on_ground = False (удаляются sample_aircraft и sample_aircraft_3)
        saver.delete_aircraft({"origin_country": "Russia", "on_ground": False})
        remaining = saver.get_aircraft()
        assert len(remaining) == 1
        assert remaining[0].id_aircraft == "DEF456"

    def test_delete_aircraft_no_match(self, tmp_path: Path, sample_aircraft: Aircraft) -> None:
        """delete_aircraft с критериями, не дающими совпадений, ничего не удаляет."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)

        saver.delete_aircraft({"origin_country": "France"})
        assert saver.get_aircraft() == [sample_aircraft]

    def test_persistence_between_instances(self, tmp_path: Path, sample_aircraft: Aircraft) -> None:
        """Данные сохраняются между разными экземплярами JSONSaver."""
        filename = tmp_path / "persist.json"

        saver1 = JSONSaver(str(filename))
        saver1.add_aircraft(sample_aircraft)

        saver2 = JSONSaver(str(filename))
        all_aircraft = saver2.get_aircraft()
        assert len(all_aircraft) == 1
        assert all_aircraft[0].id_aircraft == "ABC123"

    def test_delete_aircraft_preserves_other(
        self, tmp_path: Path, sample_aircraft: Aircraft, sample_aircraft_2: Aircraft
    ) -> None:
        """Удаление одних записей не влияет на остальные."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)
        saver.add_aircraft(sample_aircraft_2)

        saver.delete_aircraft({"id_aircraft": "ABC123"})
        remaining = saver.get_aircraft()
        assert len(remaining) == 1
        assert remaining[0].id_aircraft == "DEF456"

        # Убедимся, что удалённый не восстановится после повторной загрузки
        saver2 = JSONSaver(str(filename))
        assert len(saver2.get_aircraft()) == 1
        assert saver2.get_aircraft()[0].id_aircraft == "DEF456"

    def test_aircraft_round_trip(self, tmp_path: Path, sample_aircraft: Aircraft) -> None:
        """Сохранение и загрузка Aircraft через to_dict/from_dict сохраняет все поля."""
        filename = tmp_path / "aircraft.json"
        saver = JSONSaver(str(filename))

        saver.add_aircraft(sample_aircraft)
        loaded = saver.get_aircraft()[0]

        assert loaded.id_aircraft == sample_aircraft.id_aircraft
        assert loaded.callsign == sample_aircraft.callsign
        assert loaded.origin_country == sample_aircraft.origin_country
        assert loaded.longitude == sample_aircraft.longitude
        assert loaded.latitude == sample_aircraft.latitude
        assert loaded.vertical_rate == sample_aircraft.vertical_rate
        assert loaded.velocity == sample_aircraft.velocity
        assert loaded.geo_altitude == sample_aircraft.geo_altitude
        assert loaded.true_track == sample_aircraft.true_track
        assert loaded.squawk == sample_aircraft.squawk
        assert loaded.on_ground == sample_aircraft.on_ground
        assert loaded.bar_altitude == sample_aircraft.bar_altitude
