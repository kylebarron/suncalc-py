"""
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
"""

from datetime import datetime
from typing import Iterable, Tuple

import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None

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
    (-0.833, 'sunrise', 'sunset'),
    (-0.3, 'sunrise_end', 'sunset_start'),
    (-6, 'dawn', 'dusk'),
    (-12, 'nautical_dawn', 'nautical_dusk'),
    (-18, 'night_end', 'night'),
    (6, 'golden_hour_end', 'golden_hour')
] # yapf: disable

# date/time constants and conversions
dayMs = 1000 * 60 * 60 * 24
J1970 = 2440588
J2000 = 2451545


def to_milliseconds(date):
    # datetime.datetime
    if isinstance(date, datetime):
        return date.timestamp() * 1000

    # Pandas series of Pandas datetime objects
    if pd and pd.api.types.is_datetime64_any_dtype(date):
        # A datetime-like series coerce to int is (always?) in nanoseconds
        return date.astype('int64') / 10 ** 6

    # Single pandas Timestamp
    if pd and isinstance(date, pd.Timestamp):
        date = date.to_numpy()

    # Numpy datetime64
    if np.issubdtype(date.dtype, np.datetime64):
        return date.astype('datetime64[ms]').astype('int64')

    # Last-ditch effort
    if pd:
        return np.array(pd.to_datetime(date).astype('int64') / 10 ** 6)

    raise ValueError(f'Unknown date type: {type(date)}')


def to_julian(date):
    return to_milliseconds(date) / dayMs - 0.5 + J1970


def from_julian(j):
    ms_date = (j + 0.5 - J1970) * dayMs

    if pd:
        # If a single value, coerce to a pd.Timestamp
        if np.prod(np.array(ms_date).shape) == 1:
            return pd.to_datetime(ms_date, unit='ms')

        # .astype(datetime) is much faster than pd.to_datetime but it only works
        # on series of dates, not on a single pd.Timestamp, so I fall back to
        # pd.to_datetime for that.
        try:
            return (pd.Series(ms_date) * 1e6).astype('datetime64[ns, UTC]')
        except TypeError:
            return pd.to_datetime(ms_date, unit='ms')

    # ms_date could be iterable
    try:
        return np.array([
            datetime.utcfromtimestamp(x / 1000)
            if not np.isnan(x) else np.datetime64('NaT') for x in ms_date])

    except TypeError:
        return datetime.utcfromtimestamp(
            ms_date / 1000) if not np.isnan(ms_date) else np.datetime64('NaT')


def to_days(date):
    return to_julian(date) - J2000


# general calculations for position

# obliquity of the Earth
e = rad * 23.4397


def right_ascension(l, b):
    return atan(sin(l) * cos(e) - tan(b) * sin(e), cos(l))


def declination(l, b):
    return asin(sin(b) * cos(e) + cos(b) * sin(e) * sin(l))


def azimuth(H, phi, dec):
    return atan(sin(H), cos(H) * sin(phi) - tan(dec) * cos(phi))


def altitude(H, phi, dec):
    return asin(sin(phi) * sin(dec) + cos(phi) * cos(dec) * cos(H))


def sidereal_time(d, lw):
    return rad * (280.16 + 360.9856235 * d) - lw


def astro_refraction(h):
    # the following formula works for positive altitudes only.
    # if h = -0.08901179 a div/0 would occur.
    h = np.maximum(h, 0)

    # formula 16.4 of "Astronomical Algorithms" 2nd edition by Jean Meeus
    # (Willmann-Bell, Richmond) 1998. 1.02 / tan(h + 10.26 / (h + 5.10)) h in
    # degrees, result in arc minutes -> converted to rad:
    return 0.0002967 / np.tan(h + 0.00312536 / (h + 0.08901179))


# general sun calculations


def solar_mean_anomaly(d):
    return rad * (357.5291 + 0.98560028 * d)


def ecliptic_longitude(M):
    # equation of center
    C = rad * (1.9148 * sin(M) + 0.02 * sin(2 * M) + 0.0003 * sin(3 * M))

    # perihelion of the Earth
    P = rad * 102.9372

    return M + C + P + PI


def sun_coords(d):
    M = solar_mean_anomaly(d)
    L = ecliptic_longitude(M)

    return {'dec': declination(L, 0), 'ra': right_ascension(L, 0)}


# calculations for sun times
J0 = 0.0009


def julian_cycle(d, lw):
    return np.round(d - J0 - lw / (2 * PI))


def approx_transit(Ht, lw, n):
    return J0 + (Ht + lw) / (2 * PI) + n


def solar_transit_j(ds, M, L):
    return J2000 + ds + 0.0053 * sin(M) - 0.0069 * sin(2 * L)


def hour_angle(h, phi, d):
    return acos((sin(h) - sin(phi) * sin(d)) / (cos(phi) * cos(d)))


def observer_angle(height):
    return -2.076 * np.sqrt(height) / 60


def get_set_j(h, lw, phi, dec, n, M, L):
    """Get set time for the given sun altitude
    """
    w = hour_angle(h, phi, dec)
    a = approx_transit(w, lw, n)
    return solar_transit_j(a, M, L)


def get_position(date, lng, lat):
    """Calculate sun position for a given date and latitude/longitude
    """
    lw = rad * -lng
    phi = rad * lat
    d = to_days(date)

    c = sun_coords(d)
    H = sidereal_time(d, lw) - c['ra']

    return {
        'azimuth': azimuth(H, phi, c['dec']),
        'altitude': altitude(H, phi, c['dec'])}


def get_times(
        date,
        lng,
        lat,
        height=0,
        times: Iterable[Tuple[float, str, str]] = DEFAULT_TIMES):
    """Calculate sun times

    Calculate sun times for a given date, latitude/longitude, and,
    optionally, the observer height (in meters) relative to the horizon
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

    result = {
        'solar_noon': from_julian(Jnoon),
        'nadir': from_julian(Jnoon - 0.5)}

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


def moon_coords(d):
    """Geocentric ecliptic coordinates of the moon
    """

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

    return {'ra': right_ascension(l, b), 'dec': declination(l, b), 'dist': dt}


def getMoonPosition(date, lat, lng):

    lw = rad * -lng
    phi = rad * lat
    d = to_days(date)

    c = moon_coords(d)
    H = sidereal_time(d, lw) - c['ra']
    h = altitude(H, phi, c['dec'])

    # formula 14.1 of "Astronomical Algorithms" 2nd edition by Jean Meeus
    # (Willmann-Bell, Richmond) 1998.
    pa = atan(sin(H), tan(phi) * cos(c['dec']) - sin(c['dec']) * cos(H))

    # altitude correction for refraction
    h = h + astro_refraction(h)

    return {
        'azimuth': azimuth(H, phi, c['dec']),
        'altitude': h,
        'distance': c['dist'],
        'parallacticAngle': pa}


# calculations for illumination parameters of the moon, based on
# http://idlastro.gsfc.nasa.gov/ftp/pro/astro/mphase.pro formulas and Chapter 48
# of "Astronomical Algorithms" 2nd edition by Jean Meeus (Willmann-Bell,
# Richmond) 1998.


def getMoonIllumination(date):

    d = to_days(date)
    s = sun_coords(d)
    m = moon_coords(d)

    # distance from Earth to Sun in km
    sdist = 149598000

    phi = acos(
        sin(s['dec']) * sin(m['dec']) +
        cos(s['dec']) * cos(m['dec']) * cos(s['ra'] - m['ra']))
    inc = atan(sdist * sin(phi), m['dist'] - sdist * cos(phi)),
    angle = atan(
        cos(s['dec']) * sin(s['ra'] - m['ra']),
        sin(s['dec']) * cos(m['dec']) -
        cos(s['dec']) * sin(m['dec']) * cos(s['ra'] - m['ra']))

    return {
        'fraction': (1 + cos(inc)) / 2,
        'phase': 0.5 + 0.5 * inc * np.sign(angle) / PI,
        'angle': angle}


# def hoursLater(date, h):
#     # TODO: pythonize
#     return new Date(date.valueOf() + h * dayMs / 24)

# calculations for moon rise/set times are based on
# http://www.stargazing.net/kepler/moonrise.html article

# def getMoonTimes(date, lat, lng, inUTC):
#     var t = new Date(date);
#     if (inUTC) t.setUTCHours(0, 0, 0, 0);
#     else t.setHours(0, 0, 0, 0);
#
#     var hc = 0.133 * rad,
#         h0 = SunCalc.getMoonPosition(t, lat, lng).altitude - hc,
#         h1, h2, rise, set, a, b, xe, ye, d, roots, x1, x2, dx;
#
#     // go in 2-hour chunks, each time seeing if a 3-point quadratic curve crosses zero (which means rise or set)
#     for (var i = 1; i <= 24; i += 2) {
#         h1 = SunCalc.getMoonPosition(hoursLater(t, i), lat, lng).altitude - hc;
#         h2 = SunCalc.getMoonPosition(hoursLater(t, i + 1), lat, lng).altitude - hc;
#
#         a = (h0 + h2) / 2 - h1;
#         b = (h2 - h0) / 2;
#         xe = -b / (2 * a);
#         ye = (a * xe + b) * xe + h1;
#         d = b * b - 4 * a * h1;
#         roots = 0;
#
#         if (d >= 0) {
#             dx = Math.sqrt(d) / (Math.abs(a) * 2);
#             x1 = xe - dx;
#             x2 = xe + dx;
#             if (Math.abs(x1) <= 1) roots++;
#             if (Math.abs(x2) <= 1) roots++;
#             if (x1 < -1) x1 = x2;
#         }
#
#         if (roots === 1) {
#             if (h0 < 0) rise = i + x1;
#             else set = i + x1;
#
#         } else if (roots === 2) {
#             rise = i + (ye < 0 ? x2 : x1);
#             set = i + (ye < 0 ? x1 : x2);
#         }
#
#         if (rise && set) break;
#
#         h0 = h2;
#     }
#
#     var result = {};
#
#     if (rise) result.rise = hoursLater(t, rise);
#     if (set) result.set = hoursLater(t, set);
#
#     if (!rise && !set) result[ye > 0 ? 'alwaysUp' : 'alwaysDown'] = true;
#
#     return result;
# };
