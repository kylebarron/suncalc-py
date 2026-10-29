"""Moon functions, checked against the values in suncalc.js's test suite."""

from datetime import datetime, timezone

import numpy as np

from suncalc.suncalc import getMoonIllumination, getMoonPosition

date = datetime(2013, 3, 5, tzinfo=timezone.utc)
lat = 50.5
lng = 30.5


def test_get_moon_position():
    """getMoonPosition returns moon position data given time and location"""
    pos = getMoonPosition(date, lat, lng)
    assert np.isclose(pos["azimuth"], -0.9783999522438226)
    assert np.isclose(pos["altitude"], 0.014551482243892251)
    assert np.isclose(pos["distance"], 364121.37256256194)


def test_get_moon_illumination():
    """getMoonIllumination returns fraction, phase and angle of the moon"""
    illum = getMoonIllumination(date)
    assert np.isclose(illum["fraction"], 0.4848068202456373)
    assert np.isclose(illum["phase"], 0.7548368838538762)
    assert np.isclose(illum["angle"], 1.6732942678578346)
