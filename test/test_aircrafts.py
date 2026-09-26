from __future__ import annotations

from typing import Any, cast

import pytest

from src.aircrafts import Aircraft

# ---------- вспомогательные ----------


def make_aircraft(**overrides: Any) -> Aircraft:
    """Aircraft с минимально валидными обязательными полями + переопределения."""
    defaults: dict[str, Any] = {
        "id_aircraft": "abc123",
        "callsign": "TEST123",
        "origin_country": "Germany",
    }
    defaults.update(overrides)
    return Aircraft(**defaults)


# ---------- обязательные поля ----------


class TestAircraftRequiredFields:
    def test_creates_with_required_fields(self) -> None:
        plane = Aircraft(
            id_aircraft="abc123",
            callsign="TEST123",
            origin_country="Germany",
        )
        assert plane.id_aircraft == "abc123"
        assert plane.callsign == "TEST123"
        assert plane.origin_country == "Germany"

    def test_missing_required_fields_raises(self) -> None:
        with pytest.raises(TypeError):
            Aircraft(callsign="TEST123", origin_country="Germany")  # type: ignore[call-arg]

    def test_non_str_id_becomes_empty_string(self) -> None:
        plane = make_aircraft(id_aircraft=cast(str, 123))
        assert plane.id_aircraft == ""

    def test_non_str_origin_country_becomes_empty_string(self) -> None:
        plane = make_aircraft(origin_country=cast(str, None))
        assert plane.origin_country == ""


# ---------- callsign ----------


class TestAircraftCallsign:
    def test_callsign_is_stripped(self) -> None:
        plane = make_aircraft(callsign="  TEST123  ")
        assert plane.callsign == "TEST123"

    def test_whitespace_only_becomes_empty(self) -> None:
        assert make_aircraft(callsign="   ").callsign == ""

    def test_non_str_callsign_becomes_empty_string(self) -> None:
        plane = make_aircraft(callsign=cast(str, 42))
        assert plane.callsign == ""


# ---------- longitude ----------


class TestAircraftLongitude:
    def test_valid_float(self) -> None:
        assert make_aircraft(longitude=37.6).longitude == 37.6

    def test_valid_int_is_cast_to_float(self) -> None:
        value = make_aircraft(longitude=37).longitude
        assert value == 37.0
        assert isinstance(value, float)

    def test_boundary_180(self) -> None:
        assert make_aircraft(longitude=180.0).longitude == 180.0

    def test_boundary_minus_180(self) -> None:
        assert make_aircraft(longitude=-180.0).longitude == -180.0

    def test_out_of_range_positive_becomes_zero(self) -> None:
        assert make_aircraft(longitude=181.0).longitude == 0.0

    def test_out_of_range_negative_becomes_zero(self) -> None:
        assert make_aircraft(longitude=-181.0).longitude == 0.0

    def test_none_becomes_zero(self) -> None:
        assert make_aircraft(longitude=None).longitude == 0.0

    def test_string_becomes_zero(self) -> None:
        assert make_aircraft(longitude=cast(float, "37.6")).longitude == 0.0


# ---------- latitude ----------


class TestAircraftLatitude:
    def test_valid_float(self) -> None:
        assert make_aircraft(latitude=52.5).latitude == 52.5

    def test_boundary_90(self) -> None:
        assert make_aircraft(latitude=90.0).latitude == 90.0

    def test_boundary_minus_90(self) -> None:
        assert make_aircraft(latitude=-90.0).latitude == -90.0

    def test_out_of_range_positive_becomes_zero(self) -> None:
        assert make_aircraft(latitude=90.1).latitude == 0.0

    def test_out_of_range_negative_becomes_zero(self) -> None:
        assert make_aircraft(latitude=-90.1).latitude == 0.0

    def test_none_becomes_zero(self) -> None:
        assert make_aircraft(latitude=None).latitude == 0.0

    def test_string_becomes_zero(self) -> None:
        assert make_aircraft(latitude=cast(float, "52.5")).latitude == 0.0


# ---------- bar_altitude / geo_altitude ----------


class TestAircraftAltitudes:
    def test_bar_altitude_valid(self) -> None:
        assert make_aircraft(bar_altitude=10000.0).bar_altitude == 10000.0

    def test_bar_altitude_zero_allowed(self) -> None:
        assert make_aircraft(bar_altitude=0.0).bar_altitude == 0.0

    def test_bar_altitude_negative_becomes_zero(self) -> None:
        assert make_aircraft(bar_altitude=-1.0).bar_altitude == 0.0

    def test_bar_altitude_none_becomes_zero(self) -> None:
        assert make_aircraft(bar_altitude=None).bar_altitude == 0.0

    def test_geo_altitude_valid(self) -> None:
        plane = make_aircraft(bar_altitude=1000.0, geo_altitude=2000.0)
        assert plane.geo_altitude == 2000.0

    def test_geo_altitude_negative_falls_back_to_bar(self) -> None:
        plane = make_aircraft(bar_altitude=1500.0, geo_altitude=-10.0)
        assert plane.geo_altitude == 1500.0

    def test_geo_altitude_none_falls_back_to_bar(self) -> None:
        plane = make_aircraft(bar_altitude=1500.0, geo_altitude=None)
        assert plane.geo_altitude == 1500.0

    def test_geo_altitude_without_bar_is_zero(self) -> None:
        plane = make_aircraft(geo_altitude=None, bar_altitude=None)
        assert plane.geo_altitude == 0.0


# ---------- on_ground ----------


class TestAircraftOnGround:
    def test_none_becomes_false(self) -> None:
        assert make_aircraft(on_ground=None).on_ground is False

    def test_true_stays_true(self) -> None:
        assert make_aircraft(on_ground=True).on_ground is True

    def test_false_stays_false(self) -> None:
        assert make_aircraft(on_ground=False).on_ground is False

    def test_int_one_becomes_true(self) -> None:
        assert make_aircraft(on_ground=cast(bool, 1)).on_ground is True

    def test_int_zero_becomes_false(self) -> None:
        assert make_aircraft(on_ground=cast(bool, 0)).on_ground is False

    def test_nonempty_string_becomes_true(self) -> None:
        # bool("false") == True в Python — известная особенность этой модели
        assert make_aircraft(on_ground=cast(bool, "false")).on_ground is True

    def test_empty_string_becomes_false(self) -> None:
        assert make_aircraft(on_ground=cast(bool, "")).on_ground is False


# ---------- velocity ----------


class TestAircraftVelocity:
    def test_valid(self) -> None:
        assert make_aircraft(velocity=250.5).velocity == 250.5

    def test_int_becomes_float(self) -> None:
        value = make_aircraft(velocity=250).velocity
        assert value == 250.0
        assert isinstance(value, float)

    def test_none_becomes_zero(self) -> None:
        assert make_aircraft(velocity=None).velocity == 0.0

    def test_negative_is_allowed(self) -> None:
        assert make_aircraft(velocity=-50.0).velocity == -50.0

    def test_string_becomes_zero(self) -> None:
        assert make_aircraft(velocity=cast(float, "250")).velocity == 0.0


# ---------- true_track ----------


class TestAircraftTrueTrack:
    def test_valid(self) -> None:
        assert make_aircraft(true_track=90.0).true_track == 90.0

    def test_zero(self) -> None:
        assert make_aircraft(true_track=0).true_track == 0.0

    def test_boundary_360(self) -> None:
        assert make_aircraft(true_track=360.0).true_track == 360.0

    def test_above_360_becomes_zero(self) -> None:
        assert make_aircraft(true_track=360.1).true_track == 0.0

    def test_negative_becomes_zero(self) -> None:
        assert make_aircraft(true_track=-1.0).true_track == 0.0

    def test_none_becomes_zero(self) -> None:
        assert make_aircraft(true_track=None).true_track == 0.0


# ---------- vertical_rate ----------


class TestAircraftVerticalRate:
    def test_valid(self) -> None:
        assert make_aircraft(vertical_rate=5.5).vertical_rate == 5.5

    def test_none_becomes_zero(self) -> None:
        assert make_aircraft(vertical_rate=None).vertical_rate == 0.0

    def test_negative_is_allowed(self) -> None:
        assert make_aircraft(vertical_rate=-5.5).vertical_rate == -5.5

    def test_string_becomes_zero(self) -> None:
        assert make_aircraft(vertical_rate=cast(float, "5.5")).vertical_rate == 0.0


# ---------- squawk ----------


class TestAircraftSquawk:
    def test_valid_str(self) -> None:
        assert make_aircraft(squawk="1234").squawk == "1234"

    def test_none_becomes_default(self) -> None:
        assert make_aircraft(squawk=None).squawk == "2000"

    def test_int_becomes_default(self) -> None:
        assert make_aircraft(squawk=cast(str, 1234)).squawk == "2000"

    def test_empty_string_stays_empty(self) -> None:
        # в коде нет замены пустой строки на "2000"
        assert make_aircraft(squawk="").squawk == ""


# ---------- __repr__ ----------


class TestAircraftRepr:
    def test_starts_with_class_name(self) -> None:
        assert repr(make_aircraft()).startswith("Aircraft(")

    def test_contains_key_fields(self) -> None:
        plane = make_aircraft(callsign="TEST123")
        r = repr(plane)
        assert "TEST123" in r
        assert "abc123" in r
        assert "Germany" in r


# ---------- __eq__ ----------


class TestAircraftEq:
    def test_same_velocity_and_altitude_are_equal(self) -> None:
        a = make_aircraft(velocity=100.0, bar_altitude=1000.0, geo_altitude=1000.0)
        b = make_aircraft(velocity=100.0, bar_altitude=1000.0, geo_altitude=1000.0)
        assert a == b

    def test_different_velocity_not_equal(self) -> None:
        a = make_aircraft(velocity=100.0, bar_altitude=1000.0)
        b = make_aircraft(velocity=200.0, bar_altitude=1000.0)
        assert a != b

    def test_different_altitude_not_equal(self) -> None:
        a = make_aircraft(velocity=100.0, bar_altitude=1000.0)
        b = make_aircraft(velocity=100.0, bar_altitude=2000.0)
        assert a != b

    def test_other_fields_ignored(self) -> None:
        a = make_aircraft(callsign="AAA", velocity=100.0, bar_altitude=1000.0)
        b = make_aircraft(callsign="BBB", velocity=100.0, bar_altitude=1000.0)
        assert a == b

    def test_comparison_with_non_aircraft_returns_notimplemented(self) -> None:
        plane = make_aircraft()
        assert plane.__eq__("not an aircraft") is NotImplemented


# ---------- __lt__ ----------


class TestAircraftLt:
    def test_less_by_velocity(self) -> None:
        a = make_aircraft(velocity=100.0, bar_altitude=1000.0)
        b = make_aircraft(velocity=200.0, bar_altitude=1000.0)
        assert a < b

    def test_less_by_altitude_when_velocity_equal(self) -> None:
        a = make_aircraft(velocity=100.0, bar_altitude=1000.0)
        b = make_aircraft(velocity=100.0, bar_altitude=2000.0)
        assert a < b

    def test_not_less_when_equal(self) -> None:
        a = make_aircraft(velocity=100.0, bar_altitude=1000.0)
        b = make_aircraft(velocity=100.0, bar_altitude=1000.0)
        assert not (a < b)

    def test_comparison_with_non_aircraft_returns_notimplemented(self) -> None:
        plane = make_aircraft()
        assert plane.__lt__("not an aircraft") is NotImplemented


# ---------- сортировка ----------


class TestAircraftSorting:
    def test_sorted_by_velocity_then_altitude(self) -> None:
        a = make_aircraft(velocity=100.0, bar_altitude=1000.0)
        b = make_aircraft(velocity=200.0, bar_altitude=1000.0)
        c = make_aircraft(velocity=200.0, bar_altitude=2000.0)
        assert sorted([c, b, a]) == [a, b, c]

    def test_max_returns_highest(self) -> None:
        low = make_aircraft(velocity=100.0, bar_altitude=1000.0)
        high = make_aircraft(velocity=300.0, bar_altitude=1000.0)
        assert max(low, high) is high


# ---------- to_dict ----------


class TestAircraftToDict:
    def test_keys(self) -> None:
        d = make_aircraft().to_dict()
        assert set(d.keys()) == {
            "id_aircraft",
            "callsign",
            "country",
            "latitude",
            "longitude",
            "vertical_rate",
            "velocity",
            "altitude",
            "true_track",
            "squawk",
            "on_ground",
            "bar_altitude",
        }

    def test_values(self) -> None:
        plane = Aircraft(
            id_aircraft="abc123",
            callsign="TEST123",
            origin_country="Germany",
            latitude=52.5,
            longitude=13.4,
            vertical_rate=0.0,
            velocity=200.0,
            bar_altitude=10000.0,
            geo_altitude=10100.0,
            true_track=90.0,
            squawk="1234",
            on_ground=False,
        )
        assert plane.to_dict() == {
            "id_aircraft": "abc123",
            "callsign": "TEST123",
            "country": "Germany",
            "latitude": 52.5,
            "longitude": 13.4,
            "vertical_rate": 0.0,
            "velocity": 200.0,
            "altitude": 10100.0,
            "true_track": 90.0,
            "squawk": "1234",
            "on_ground": False,
            "bar_altitude": 10000.0,
        }

    def test_altitude_uses_geo_altitude(self) -> None:
        plane = make_aircraft(bar_altitude=1000.0, geo_altitude=2000.0)
        assert plane.to_dict()["altitude"] == 2000.0


# ---------- from_dict ----------


class TestAircraftFromDict:
    def test_full_dict(self) -> None:
        data = {
            "id_aircraft": "abc123",
            "callsign": "TEST123",
            "country": "Germany",
            "latitude": 52.5,
            "longitude": 13.4,
            "vertical_rate": 0.0,
            "velocity": 200.0,
            "altitude": 10000.0,
            "true_track": 90.0,
            "squawk": "1234",
            "on_ground": False,
            "bar_altitude": 9900.0,
        }
        plane = Aircraft.from_dict(data)
        assert plane.id_aircraft == "abc123"
        assert plane.callsign == "TEST123"
        assert plane.origin_country == "Germany"
        assert plane.latitude == 52.5
        assert plane.longitude == 13.4
        assert plane.velocity == 200.0
        assert plane.geo_altitude == 10000.0
        assert plane.bar_altitude == 9900.0
        assert plane.squawk == "1234"
        assert plane.on_ground is False

    def test_empty_dict_gives_defaults(self) -> None:
        plane = Aircraft.from_dict({})
        assert plane.id_aircraft == ""
        assert plane.callsign == ""
        assert plane.origin_country == ""
        assert plane.longitude == 0.0
        assert plane.latitude == 0.0
        assert plane.velocity == 0.0
        assert plane.squawk == "2000"

    def test_country_key_maps_to_origin_country(self) -> None:
        plane = Aircraft.from_dict({"country": "France"})
        assert plane.origin_country == "France"

    def test_altitude_key_maps_to_geo_altitude(self) -> None:
        plane = Aircraft.from_dict({"altitude": 12345.0})
        assert plane.geo_altitude == 12345.0

    def test_roundtrip_via_to_dict(self) -> None:
        original = Aircraft(
            id_aircraft="abc123",
            callsign="TEST123",
            origin_country="Germany",
            latitude=52.5,
            longitude=13.4,
            velocity=200.0,
            bar_altitude=10000.0,
            geo_altitude=10100.0,
        )
        restored = Aircraft.from_dict(original.to_dict())
        assert restored.id_aircraft == original.id_aircraft
        assert restored.callsign == original.callsign
        assert restored.origin_country == original.origin_country
        assert restored.latitude == original.latitude
        assert restored.longitude == original.longitude
        assert restored.velocity == original.velocity
        assert restored.geo_altitude == original.geo_altitude
        assert restored.bar_altitude == original.bar_altitude
