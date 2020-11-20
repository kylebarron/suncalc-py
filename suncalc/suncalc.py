"""
TODO: include suncalc.js' BSD-2-clause license
"""
import numpy as np

# shortcuts for easier to read formulas
PI = np.pi
sin = np.sin
cos = np.cos
tan = np.tan
asin = np.arcsin
atan = np.arctan2
acos = np.arccos
rad = PI / 180

# date/time constants and conversions
dayMs = 1000 * 60 * 60 * 24
J1970 = 2440588
J2000 = 2451545

# function toJulian(date) { return date.valueOf() / dayMs - 0.5 + J1970; }
# function fromJulian(j)  { return new Date((j + 0.5 - J1970) * dayMs); }
# function toDays(date)   { return toJulian(date) - J2000; }

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

def siderealTime(d, lw):
    return rad * (280.16 + 360.9856235 * d) - lw

def astro_refraction(h):
    # the following formula works for positive altitudes only.
    # if h = -0.08901179 a div/0 would occur.
    h = max(h, 0)

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

    return {
        'dec': declination(L, 0),
        'ra': right_ascension(L, 0)
    }


SunCalc = {}


def get_position(date, lat, lng):
    """Calculate sun position for a given date and latitude/longitude
    """

    lw  = rad * -lng
    phi = rad * lat
    d   = toDays(date)

    c  = sun_coords(d)
    H  = siderealTime(d, lw) - c['ra']

    return {
        'azimuth': azimuth(H, phi, c.dec),
        'altitude': altitude(H, phi, c.dec)
    }

# sun times configuration (angle, morning name, evening name)
times = [
    (-0.833, 'sunrise',       'sunset'      ),
    (  -0.3, 'sunriseEnd',    'sunsetStart' ),
    (    -6, 'dawn',          'dusk'        ),
    (   -12, 'nauticalDawn',  'nauticalDusk'),
    (   -18, 'nightEnd',      'night'       ),
    (     6, 'goldenHourEnd', 'goldenHour'  )
]

def add_time(angle, rise_name, set_name):
    """Add a custom time to the times config
    """
    times.append((angle, rise_name, set_name))


