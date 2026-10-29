"""Sun position and sunlight phases, ported from suncalc.js.

suncalc-py is ported from suncalc.js under the BSD-2-Clause license.

Copyright (c) 2014, Vladimir Agafonkin
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""  # noqa: E501

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None

if TYPE_CHECKING:
    from collections.abc import Iterable

    import numpy.typing as npt
    from pandas import Series

    # Calculations work on floats, numpy arrays and pandas Series alike
    Values = float | np.ndarray | Series

# shortcuts for easier to read formulas
PI = np.pi
sin = np.sin
cos = np.cos
tan = np.tan
asin = np.arcsin
atan = np.arctan2
acos = np.arccos
rad = PI / 180

# sun times configuration (angle, morning name, evening name)
DEFAULT_TIMES = [
    (-0.833, "sunrise", "sunset"),
    (-0.3, "sunrise_end", "sunset_start"),
    (-6, "dawn", "dusk"),
    (-12, "nautical_dawn", "nautical_dusk"),
    (-18, "night_end", "night"),
    (6, "golden_hour_end", "golden_hour"),
]

# date/time constants and conversions
dayMs = 1000 * 60 * 60 * 24
J1970 = 2440588
J2000 = 2451545


def to_milliseconds(date: datetime | npt.ArrayLike) -> Values:
    """Convert dates to milliseconds since the Unix epoch. NaT becomes NaN."""
    # datetime.datetime
    if isinstance(date, datetime):
        # pd.NaT is a datetime too
        if pd and date is pd.NaT:
            return np.nan
        # Naive datetimes are UTC, not local time
        if date.tzinfo is None:
            date = date.replace(tzinfo=UTC)
        return date.timestamp() * 1000

    # Pandas Series or DatetimeIndex of any resolution (pandas 3 infers
    # microseconds by default); a numpy datetime64 array goes to the numpy
    # branch below
    if (
        pd
        and isinstance(date, pd.Series)
        and pd.api.types.is_datetime64_any_dtype(date)
    ):
        ms = date.dt.as_unit("ns").astype("int64") / 10**6
        return ms.where(date.notna())
    if pd and isinstance(date, pd.DatetimeIndex):
        ms = date.as_unit("ns").astype("int64") / 10**6
        return ms.where(date.notna())

    # Single pandas Timestamp
    if pd and isinstance(date, pd.Timestamp):
        date = date.to_numpy()

    # Numpy datetime64
    if np.issubdtype(date.dtype, np.datetime64):
        return (date - np.datetime64(0, "ms")) / np.timedelta64(1, "ms")

    # Last-ditch effort
    if pd:
        date = pd.to_datetime(date)
        ms = date.as_unit("ns").astype("int64") / 10**6
        return np.array(ms.where(date.notna()))

    raise ValueError(f"Unknown date type: {type(date)}")


def to_julian(date: datetime | npt.ArrayLike) -> Values:
    """Convert dates to Julian days."""
    return to_milliseconds(date) / dayMs - 0.5 + J1970


def from_julian(j: Values) -> datetime | np.datetime64 | np.ndarray | Series:
    """Convert Julian days to dates in UTC.

    Returns a `pd.Timestamp` for a single value and a `pd.Series` of
    timezone-aware datetimes otherwise. Without pandas, returns a `datetime`
    or a numpy array of datetimes.
    """
    ms_date = (j + 0.5 - J1970) * dayMs

    if pd:
        # If a single value, coerce to a pd.Timestamp
        if np.prod(np.array(ms_date).shape) == 1:
            return pd.to_datetime(ms_date, unit="ms")

        # .astype(datetime) is much faster than pd.to_datetime but it only works
        # on series of dates, not on a single pd.Timestamp, so I fall back to
        # pd.to_datetime for that.
        try:
            return (pd.Series(ms_date) * 1e6).astype("datetime64[ns, UTC]")
        except TypeError:
            return pd.to_datetime(ms_date, unit="ms")

    # ms_date could be iterable
    try:
        return np.array(
            [
                _utc_from_ms(x) if not np.isnan(x) else np.datetime64("NaT", "us")
                for x in ms_date
            ]
        )

    except TypeError:
        return (
            _utc_from_ms(ms_date)
            if not np.isnan(ms_date)
            else np.datetime64("NaT", "us")
        )


def _utc_from_ms(ms: float) -> datetime:
    """Convert milliseconds since the Unix epoch to a naive datetime in UTC."""
    return datetime.fromtimestamp(ms / 1000, tz=UTC).replace(tzinfo=None)


def to_days(date: datetime | npt.ArrayLike) -> Values:
    """Convert dates to days since J2000."""
    return to_julian(date) - J2000


# general calculations for position

# obliquity of the Earth
e = rad * 23.4397


def right_ascension(l: Values, b: Values) -> Values:
    """Right ascension from ecliptic longitude and latitude."""
    return atan(sin(l) * cos(e) - tan(b) * sin(e), cos(l))


def declination(l: Values, b: Values) -> Values:
    """Declination from ecliptic longitude and latitude."""
    return asin(sin(b) * cos(e) + cos(b) * sin(e) * sin(l))


def azimuth(H: Values, phi: Values, dec: Values) -> Values:
    """Azimuth from hour angle, latitude and declination."""
    return atan(sin(H), cos(H) * sin(phi) - tan(dec) * cos(phi))


def altitude(H: Values, phi: Values, dec: Values) -> Values:
    """Altitude from hour angle, latitude and declination."""
    return asin(sin(phi) * sin(dec) + cos(phi) * cos(dec) * cos(H))


def sidereal_time(d: Values, lw: Values) -> Values:
    """Sidereal time from days since J2000 and west longitude."""
    return rad * (280.16 + 360.9856235 * d) - lw


def astro_refraction(h: Values) -> Values:
    """Atmospheric refraction for an altitude, in radians."""
    # the following formula works for positive altitudes only.
    # if h = -0.08901179 a div/0 would occur.
    h = np.maximum(h, 0)

    # formula 16.4 of "Astronomical Algorithms" 2nd edition by Jean Meeus
    # (Willmann-Bell, Richmond) 1998. 1.02 / tan(h + 10.26 / (h + 5.10)) h in
    # degrees, result in arc minutes -> converted to rad:
    return 0.0002967 / np.tan(h + 0.00312536 / (h + 0.08901179))


# general sun calculations


def solar_mean_anomaly(d: Values) -> Values:
    """Solar mean anomaly from days since J2000."""
    return rad * (357.5291 + 0.98560028 * d)


def ecliptic_longitude(M: Values) -> Values:
    """Ecliptic longitude of the sun from its mean anomaly."""
    # equation of center
    C = rad * (1.9148 * sin(M) + 0.02 * sin(2 * M) + 0.0003 * sin(3 * M))

    # perihelion of the Earth
    P = rad * 102.9372

    return M + C + P + PI


def sun_coords(d: Values) -> dict[str, Values]:
    """Declination and right ascension of the sun from days since J2000."""
    M = solar_mean_anomaly(d)
    L = ecliptic_longitude(M)

    return {"dec": declination(L, 0), "ra": right_ascension(L, 0)}


# calculations for sun times
J0 = 0.0009


def julian_cycle(d: Values, lw: Values) -> Values:
    """Julian cycle from days since J2000 and west longitude."""
    return np.round(d - J0 - lw / (2 * PI))


def approx_transit(Ht: Values, lw: Values, n: Values) -> Values:
    """Approximate solar transit in days since J2000."""
    return J0 + (Ht + lw) / (2 * PI) + n


def solar_transit_j(ds: Values, M: Values, L: Values) -> Values:
    """Solar transit as a Julian day."""
    return J2000 + ds + 0.0053 * sin(M) - 0.0069 * sin(2 * L)


def hour_angle(h: Values, phi: Values, d: Values) -> Values:
    """Hour angle at which the sun reaches altitude `h`.

    NaN where the sun never reaches `h` that day.
    """
    with np.errstate(invalid="ignore"):
        return acos((sin(h) - sin(phi) * sin(d)) / (cos(phi) * cos(d)))


def observer_angle(height: Values) -> Values:
    """Horizon dip, in degrees, for an observer `height` meters up."""
    return -2.076 * np.sqrt(height) / 60


def get_set_j(  # noqa: PLR0913, PLR0917 (mirrors getSetJ in suncalc.js)
    h: Values,
    lw: Values,
    phi: Values,
    dec: Values,
    n: Values,
    M: Values,
    L: Values,
) -> Values:
    """Get set time for the given sun altitude."""
    w = hour_angle(h, phi, dec)
    a = approx_transit(w, lw, n)
    return solar_transit_j(a, M, L)


def get_position(
    date: datetime | npt.ArrayLike,
    lng: npt.ArrayLike,
    lat: npt.ArrayLike,
) -> dict[str, Any]:
    """Calculate sun position for a given date and longitude/latitude.

    Args:
        date: Date and time to find the sun position of, as a `datetime`, a
            pandas `Timestamp` or `Series` of datetimes, or a numpy
            `datetime64` array. Naive datetimes are treated as UTC.
        lng: Longitude, in degrees.
        lat: Latitude, in degrees.

    Returns:
        A dict with keys `azimuth` and `altitude`, in radians. Azimuth is the
            direction along the horizon, measured from south to west: `0` is
            south and `pi * 3/4` is northwest. Altitude is the angle above the
            horizon: `0` is the horizon and `pi/2` is the zenith. The values
            are floats for single inputs and arrays (or pandas Series) for
            array inputs, and NaN where `date` is `NaT`.

    """
    lw = rad * -lng
    phi = rad * lat
    d = to_days(date)

    c = sun_coords(d)
    H = sidereal_time(d, lw) - c["ra"]

    return {
        "azimuth": azimuth(H, phi, c["dec"]),
        "altitude": altitude(H, phi, c["dec"]),
    }


def get_times(
    date: datetime | npt.ArrayLike,
    lng: npt.ArrayLike,
    lat: npt.ArrayLike,
    height: npt.ArrayLike = 0,
    times: Iterable[tuple[float, str, str]] = DEFAULT_TIMES,
) -> dict[str, Any]:
    """Calculate sun times for a given date, longitude/latitude, and height.

    Args:
        date: Date to find sunlight phases of, as a `datetime`, a pandas
            `Timestamp` or `Series` of datetimes, or a numpy `datetime64`
            array. Naive datetimes are treated as UTC.
        lng: Longitude, in degrees.
        lat: Latitude, in degrees.
        height: Observer height, in meters, relative to the horizon.
        times: Sunlight phases to compute, as tuples of `(angle, morning name,
            evening name)`, where `angle` is the sun's altitude in degrees.
            Defaults to `DEFAULT_TIMES`.

    Returns:
        A dict with keys `solar_noon`, `nadir`, and the morning and evening
            names in `times`. The times are in UTC. For single inputs, they're
            naive `pd.Timestamp`s (or `datetime`s without pandas). For array
            inputs, they're pandas Series of timezone-aware datetimes (or numpy
            arrays without pandas). Times the sun doesn't reach that day, like
            night in summer at high latitudes, are `NaT`, as are all times
            where `date` is `NaT`.

    """
    # If inputs are vectors (or some list-like type), then coerce them to
    # numpy arrays
    #
    # When inputs are pandas series, then intermediate objects will also be
    # pandas series, and you won't be able to do 2d broadcasting.
    try:
        len(date)
        len(lat)
        len(lng)
        array_input = True
        date = np.array(date)
        lat = np.array(lat)
        lng = np.array(lng)
    except TypeError:
        array_input = False

    lw = rad * -lng
    phi = rad * lat

    dh = observer_angle(height)

    d = to_days(date)
    n = julian_cycle(d, lw)
    ds = approx_transit(0, lw, n)

    M = solar_mean_anomaly(ds)
    L = ecliptic_longitude(M)
    dec = declination(L, 0)

    Jnoon = solar_transit_j(ds, M, L)

    result = {"solar_noon": from_julian(Jnoon), "nadir": from_julian(Jnoon - 0.5)}

    angles = np.array([time[0] for time in times])
    h0 = (angles + dh) * rad

    # If array input, add an axis to allow 2d broadcasting
    if array_input:
        h0 = h0[:, np.newaxis]

    # Need to add an axis for 2D broadcasting
    Jset = get_set_j(h0, lw, phi, dec, n, M, L)
    Jrise = Jnoon - (Jset - Jnoon)

    for idx, time in enumerate(times):
        if array_input:
            result[time[1]] = from_julian(Jrise[idx, :])
            result[time[2]] = from_julian(Jset[idx, :])
        else:
            result[time[1]] = from_julian(Jrise[idx])
            result[time[2]] = from_julian(Jset[idx])

    return result


# moon calculations, based on http://aa.quae.nl/en/reken/hemelpositie.html
# formulas


def moon_coords(d: Values) -> dict[str, Values]:
    """Geocentric ecliptic coordinates of the moon."""
    # ecliptic longitude
    L = rad * (218.316 + 13.176396 * d)
    # mean anomaly
    M = rad * (134.963 + 13.064993 * d)
    # mean distance
    F = rad * (93.272 + 13.229350 * d)

    # longitude
    l = L + rad * 6.289 * sin(M)
    # latitude
    b = rad * 5.128 * sin(F)
    # distance to the moon in km
    dt = 385001 - 20905 * cos(M)

    return {"ra": right_ascension(l, b), "dec": declination(l, b), "dist": dt}


def getMoonPosition(  # noqa: N802 (public name kept for backwards compatibility)
    date: datetime | npt.ArrayLike,
    lat: npt.ArrayLike,
    lng: npt.ArrayLike,
) -> dict[str, Any]:
    """Calculate moon position for a given date and latitude/longitude.

    Unlike `get_position`, this takes latitude before longitude, as in
    suncalc.js.

    Args:
        date: Date and time to find the moon position of.
        lat: Latitude, in degrees.
        lng: Longitude, in degrees.

    Returns:
        A dict with keys `azimuth` and `altitude` (in radians, as in
            `get_position`), `distance` (to the moon, in kilometers), and
            `parallacticAngle` (in radians).

    """
    lw = rad * -lng
    phi = rad * lat
    d = to_days(date)

    c = moon_coords(d)
    H = sidereal_time(d, lw) - c["ra"]
    h = altitude(H, phi, c["dec"])

    # formula 14.1 of "Astronomical Algorithms" 2nd edition by Jean Meeus
    # (Willmann-Bell, Richmond) 1998.
    pa = atan(sin(H), tan(phi) * cos(c["dec"]) - sin(c["dec"]) * cos(H))

    # altitude correction for refraction
    h = h + astro_refraction(h)

    return {
        "azimuth": azimuth(H, phi, c["dec"]),
        "altitude": h,
        "distance": c["dist"],
        "parallacticAngle": pa,
    }


# calculations for illumination parameters of the moon, based on
# http://idlastro.gsfc.nasa.gov/ftp/pro/astro/mphase.pro formulas and Chapter 48
# of "Astronomical Algorithms" 2nd edition by Jean Meeus (Willmann-Bell,
# Richmond) 1998.


def getMoonIllumination(  # noqa: N802 (public name kept for backwards compatibility)
    date: datetime | npt.ArrayLike,
) -> dict[str, Any]:
    """Calculate the moon's illumination for a given date.

    Args:
        date: Date and time to find the moon's illumination of.

    Returns:
        A dict with keys `fraction` (illuminated fraction of the moon, from `0`
            for a new moon to `1` for a full moon), `phase` (from `0` to `1`:
            `0` is a new moon, `0.5` a full moon), and `angle` (midpoint angle
            in radians of the illuminated limb, measured eastward from the
            north point of the disk).

    """
    d = to_days(date)
    s = sun_coords(d)
    m = moon_coords(d)

    # distance from Earth to Sun in km
    sdist = 149598000

    phi = acos(
        sin(s["dec"]) * sin(m["dec"])
        + cos(s["dec"]) * cos(m["dec"]) * cos(s["ra"] - m["ra"])
    )
    inc = atan(sdist * sin(phi), m["dist"] - sdist * cos(phi))
    angle = atan(
        cos(s["dec"]) * sin(s["ra"] - m["ra"]),
        sin(s["dec"]) * cos(m["dec"])
        - cos(s["dec"]) * sin(m["dec"]) * cos(s["ra"] - m["ra"]),
    )

    return {
        "fraction": (1 + cos(inc)) / 2,
        "phase": 0.5 + 0.5 * inc * np.sign(angle) / PI,
        "angle": angle,
    }


# getMoonTimes from suncalc.js isn't ported yet
