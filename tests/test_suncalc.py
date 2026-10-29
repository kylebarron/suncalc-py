from datetime import datetime, timezone

import numpy as np
import pandas as pd

from suncalc import get_position, get_times

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


def test_get_position():
    """getPosition returns azimuth and altitude for the given time and location"""
    pos = get_position(date, lng, lat)
    assert np.isclose(pos["azimuth"], -2.5003175907168385)
    assert np.isclose(pos["altitude"], -0.7000406838781611)


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


def test_get_position_pandas_single_timestamp():
    ts_date = pd.Timestamp(date)

    pos = get_position(ts_date, lng, lat)
    assert np.isclose(pos["azimuth"], -2.5003175907168385)
    assert np.isclose(pos["altitude"], -0.7000406838781611)


def test_get_position_pandas_datetime_series():
    df = pd.DataFrame({"date": [date] * 3, "lat": [lat] * 3, "lng": [lng] * 3})

    pos = pd.DataFrame(get_position(df["date"], df["lng"], df["lat"]))

    assert pos.shape == (3, 2)
    assert all(x in pos.columns for x in ["azimuth", "altitude"])
    assert pos.dtypes["azimuth"] == np.dtype("float64")
    assert pos.dtypes["altitude"] == np.dtype("float64")

    assert np.isclose(pos["azimuth"].iloc[0], -2.5003175907168385)
    assert np.isclose(pos["altitude"].iloc[0], -0.7000406838781611)


def test_get_position_datetime64_any_resolution():
    """DatetimeIndex, Series and numpy arrays agree with the scalar path at
    every datetime64 resolution, tz-aware or naive (UTC)."""
    expected = get_position(date, lng, lat)
    aware = pd.DatetimeIndex([date] * 3)
    for unit in ["s", "ms", "us", "ns"]:
        index = aware.as_unit(unit)
        for dates in [
            index,
            index.tz_convert(None),
            pd.Series(index),
            pd.Series(index.tz_convert(None)),
            index.tz_convert(None).to_numpy(),
        ]:
            pos = get_position(dates, lng, lat)
            assert np.allclose(pos["azimuth"], expected["azimuth"])
            assert np.allclose(pos["altitude"], expected["altitude"])

    # A Series keeps its own index
    series = pd.Series(aware.as_unit("us"), index=[10, 11, 12])
    pos = get_position(series, lng, lat)
    assert list(pos["altitude"].index) == [10, 11, 12]


def test_get_times_pandas_single():
    times = get_times(date, lng, lat)

    assert isinstance(times["solar_noon"], pd.Timestamp)


def test_get_times_datetime_single():
    times = get_times(date, lng, lat)

    # This is true because pd.Timestamp is an instance of datetime.datetime
    assert isinstance(times["solar_noon"], datetime)


def test_get_times_arrays():
    df = pd.DataFrame({"date": [date] * 3, "lat": [lat] * 3, "lng": [lng] * 3})

    times = pd.DataFrame(get_times(df["date"], df["lng"], df["lat"]))

    assert pd.api.types.is_datetime64_any_dtype(times["solar_noon"])

    assert (
        times["solar_noon"].iloc[0].strftime("%Y-%m-%dT%H:%M:%SZ")
        == TEST_TIMES["solar_noon"]
    )


def test_get_times_for_high_latitudes():
    """getTimes may fail (maybe only on Windows?) for high latitudes in the summer

    See https://github.com/kylebarron/suncalc-py/issues/4
    """
    date = datetime(2020, 5, 26, 0, 0, 0, tzinfo=timezone.utc)
    lng = -114.0719
    lat = 51.0447

    # Make sure this doesn't raise an exception (though it will emit a warning
    # due to a division error)
    get_times(date, lng, lat)
