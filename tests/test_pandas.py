from datetime import datetime, timezone

import numpy as np
import pytest

from suncalc import get_position, get_times

pd = pytest.importorskip("pandas")

date = datetime(2013, 3, 5, tzinfo=timezone.utc)
lat = 50.5
lng = 30.5


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


def test_get_times_arrays():
    df = pd.DataFrame({"date": [date] * 3, "lat": [lat] * 3, "lng": [lng] * 3})

    times = pd.DataFrame(get_times(df["date"], df["lng"], df["lat"]))

    assert pd.api.types.is_datetime64_any_dtype(times["solar_noon"])

    assert (
        times["solar_noon"].iloc[0].strftime("%Y-%m-%dT%H:%M:%SZ")
        == "2013-03-05T10:10:57Z"
    )


@pytest.mark.parametrize("tz", [None, "UTC"])
def test_get_times_series_matches_single_dates(tz):
    """Each row of the vectorized result matches the result for that date"""
    dates = pd.Series(pd.date_range("2023-01-01", periods=3, freq="D", tz=tz))
    lngs = [lng, 0, -120]
    lats = [lat, 0, 45]

    times = get_times(dates, lngs, lats)

    for i in range(3):
        single = get_times(dates[i], lngs[i], lats[i])
        for key, value in single.items():
            expected = value.tz_localize("UTC")
            assert abs(times[key].iloc[i] - expected) < pd.Timedelta(1, "ms")


def test_get_times_series_that_dont_occur():
    """Times the sun doesn't reach are NaT"""
    dates = pd.Series(pd.to_datetime(["2023-05-24", "2023-01-01"], utc=True))

    times = get_times(dates, [0, 0], [51.5, 51.5])

    assert times["night"].isna().tolist() == [True, False]
    assert times["sunrise"].notna().all()


def test_get_position_nat():
    """NaT gives NaN instead of the position on 1677-09-21"""
    pos = get_position(pd.NaT, lng, lat)
    assert np.isnan(pos["azimuth"])
    assert np.isnan(pos["altitude"])


def test_get_position_series_with_nat():
    dates = pd.Series(pd.to_datetime([None, date], utc=True))

    pos = get_position(dates, lng, lat)

    assert pos["altitude"].isna().tolist() == [True, False]
    assert np.isclose(pos["altitude"].iloc[1], -0.7000406838781611)


def test_get_position_datetime_index_with_nat():
    """The example from #19"""
    dates = pd.to_datetime([None, None], unit="s", utc=True)

    pos = get_position(dates, 0, 0)

    assert np.isnan(pos["azimuth"]).all()
    assert np.isnan(pos["altitude"]).all()


def test_get_times_nat():
    times = get_times(pd.NaT, lng, lat)
    assert all(value is pd.NaT for value in times.values())


def test_get_times_series_with_nat():
    dates = pd.Series(pd.to_datetime([None, date], utc=True))

    times = get_times(dates, [lng, lng], [lat, lat])

    expected = get_times(date, lng, lat)
    for key, value in times.items():
        assert value.isna().tolist() == [True, False]
        assert abs(value.iloc[1] - expected[key].tz_localize("UTC")) < pd.Timedelta(
            1, "ms"
        )
