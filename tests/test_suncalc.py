import time
from datetime import datetime, timezone
from importlib.metadata import version

import numpy as np
import pytest

import suncalc
from suncalc import get_position, get_times
from suncalc.suncalc import DEFAULT_TIMES

date = datetime(2013, 3, 5, tzinfo=timezone.utc)
lat = 50.5
lng = 30.5
height = 2000

TEST_TIMES = {
    "solar_noon": "2013-03-05T10:10:57Z",
    "nadir": "2013-03-04T22:10:57Z",
    "sunrise": "2013-03-05T04:34:56Z",
    "sunset": "2013-03-05T15:46:57Z",
    "sunrise_end": "2013-03-05T04:38:19Z",
    "sunset_start": "2013-03-05T15:43:34Z",
    "dawn": "2013-03-05T04:02:17Z",
    "dusk": "2013-03-05T16:19:36Z",
    "nautical_dawn": "2013-03-05T03:24:31Z",
    "nautical_dusk": "2013-03-05T16:57:22Z",
    "night_end": "2013-03-05T02:46:17Z",
    "night": "2013-03-05T17:35:36Z",
    "golden_hour_end": "2013-03-05T05:19:01Z",
    "golden_hour": "2013-03-05T15:02:52Z",
}

HEIGHT_TEST_TIMES = {
    "solar_noon": "2013-03-05T10:10:57Z",
    "nadir": "2013-03-04T22:10:57Z",
    "sunrise": "2013-03-05T04:25:07Z",
    "sunset": "2013-03-05T15:56:46Z",
}


def is_nat(value: object) -> bool:
    """Whether a value is pandas' `NaT` or numpy's `datetime64("NaT")`."""
    return str(value) == "NaT"


@pytest.fixture
def local_timezone_not_utc(monkeypatch):
    """Set the local timezone to one that isn't UTC."""
    if not hasattr(time, "tzset"):
        pytest.skip("time.tzset is only available on Unix")
    monkeypatch.setenv("TZ", "Europe/Berlin")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.mark.usefixtures("local_timezone_not_utc")
def test_get_position_naive_datetime_is_utc():
    naive = datetime(2013, 3, 5, 12)  # noqa: DTZ001
    pos = get_position(naive, lng, lat)
    expected = get_position(naive.replace(tzinfo=timezone.utc), lng, lat)
    assert pos == expected


@pytest.mark.usefixtures("local_timezone_not_utc")
def test_get_times_naive_datetime_is_utc():
    """00:30 UTC and 00:30 in Berlin are on different sides of the solar day"""
    naive = datetime(2013, 3, 5, 0, 30)  # noqa: DTZ001
    times = get_times(naive, 0, 0)
    expected = get_times(naive.replace(tzinfo=timezone.utc), 0, 0)
    assert times == expected


@pytest.mark.usefixtures("local_timezone_not_utc")
def test_get_position_at_solar_noon():
    """The sun is due south at solar noon, for times get_times returns (#6)"""
    times = get_times(date, lng, lat)
    pos = get_position(times["solar_noon"], lng, lat)
    assert abs(pos["azimuth"]) < 0.01


def test_get_position():
    """getPosition returns azimuth and altitude for the given time and location"""
    pos = get_position(date, lng, lat)
    assert np.isclose(pos["azimuth"], -2.5003175907168385)
    assert np.isclose(pos["altitude"], -0.7000406838781611)


def test_get_position_coordinate_arrays():
    """Arrays of longitudes and latitudes broadcast against a single date"""
    pos = get_position(date, np.array([lng, 0]), np.array([lat, 0]))
    expected = [get_position(date, lng, lat), get_position(date, 0, 0)]
    np.testing.assert_allclose(pos["azimuth"], [p["azimuth"] for p in expected])
    np.testing.assert_allclose(pos["altitude"], [p["altitude"] for p in expected])


def test_get_position_datetime64_nat():
    """NaT gives NaN instead of the position on 1677-09-21"""
    dates = np.array(["NaT", "2013-03-05"], dtype="datetime64[ms]")

    pos = get_position(dates, lng, lat)

    assert np.isnan(pos["altitude"][0])
    assert np.isclose(pos["altitude"][1], -0.7000406838781611)


@pytest.mark.parametrize("unit", ["M", "D", "s", "ms", "us", "ns"])
def test_get_position_datetime64_units(unit):
    dates = np.array(["2013-03-01"], dtype="datetime64[D]").astype(
        f"datetime64[{unit}]"
    )

    pos = get_position(dates, lng, lat)

    expected = get_position(datetime(2013, 3, 1, tzinfo=timezone.utc), lng, lat)
    np.testing.assert_allclose(pos["altitude"], expected["altitude"])


def test_get_times():
    """getTimes returns sun phases for the given date and location"""
    times = get_times(date, lng, lat)
    for key, value in TEST_TIMES.items():
        assert times[key].strftime("%Y-%m-%dT%H:%M:%SZ") == value


def test_get_times_height():
    """getTimes adjusts sun phases when additionally given the observer height"""
    times = get_times(date, lng, lat, height)
    for key, value in HEIGHT_TEST_TIMES.items():
        assert times[key].strftime("%Y-%m-%dT%H:%M:%SZ") == value


def test_get_times_datetime_single():
    times = get_times(date, lng, lat)

    # This is true because pd.Timestamp is an instance of datetime.datetime
    assert isinstance(times["solar_noon"], datetime)


def test_get_times_default_keys():
    times = get_times(date, lng, lat)
    names = {
        name for _, morning, evening in DEFAULT_TIMES for name in (morning, evening)
    }
    assert set(times) == {"solar_noon", "nadir"} | names


def test_get_times_order():
    """Morning times come before solar noon, and evening times after"""
    times = get_times(date, lng, lat)
    assert times["nadir"] < times["solar_noon"]
    for _, morning, evening in DEFAULT_TIMES:
        assert times[morning] < times["solar_noon"] < times[evening]


def test_get_times_custom_times():
    """Custom times match the default times with the same angle"""
    times = get_times(date, lng, lat, times=[(-6, "civil_dawn", "civil_dusk")])
    default = get_times(date, lng, lat)
    assert set(times) == {"solar_noon", "nadir", "civil_dawn", "civil_dusk"}
    assert times["civil_dawn"] == default["dawn"]
    assert times["civil_dusk"] == default["dusk"]


def test_get_times_that_dont_occur():
    """Times the sun doesn't reach are NaT, like night at 51.5N in late May"""
    times = get_times(datetime(2023, 5, 24, tzinfo=timezone.utc), 0, 51.5)
    assert is_nat(times["night_end"])
    assert is_nat(times["night"])
    assert not is_nat(times["nautical_dusk"])


def test_get_times_for_high_latitudes():
    """getTimes may fail (maybe only on Windows?) for high latitudes in the summer

    See https://github.com/kylebarron/suncalc-py/issues/4
    """
    date = datetime(2020, 5, 26, 0, 0, 0, tzinfo=timezone.utc)
    lng = -114.0719
    lat = 51.0447

    # Make sure this doesn't raise an exception
    get_times(date, lng, lat)


def test_version():
    assert suncalc.__version__ == version("suncalc")
