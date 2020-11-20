from datetime import datetime, timezone

import numpy as np

from suncalc import SunCalc

date = datetime(2013, 3, 5, tzinfo=timezone.utc)
lat = 50.5
lng = 30.5
height = 2000

testTimes = {
    'solarNoon': '2013-03-05T10:10:57Z',
    'nadir': '2013-03-04T22:10:57Z',
    'sunrise': '2013-03-05T04:34:56Z',
    'sunset': '2013-03-05T15:46:57Z',
    'sunriseEnd': '2013-03-05T04:38:19Z',
    'sunsetStart': '2013-03-05T15:43:34Z',
    'dawn': '2013-03-05T04:02:17Z',
    'dusk': '2013-03-05T16:19:36Z',
    'nauticalDawn': '2013-03-05T03:24:31Z',
    'nauticalDusk': '2013-03-05T16:57:22Z',
    'nightEnd': '2013-03-05T02:46:17Z',
    'night': '2013-03-05T17:35:36Z',
    'goldenHourEnd': '2013-03-05T05:19:01Z',
    'goldenHour': '2013-03-05T15:02:52Z'}

heightTestTimes = {
    'solarNoon': '2013-03-05T10:10:57Z',
    'nadir': '2013-03-04T22:10:57Z',
    'sunrise': '2013-03-05T04:25:07Z',
    'sunset': '2013-03-05T15:56:46Z'}


def test_get_position():
    """getPosition returns azimuth and altitude for the given time and location
    """
    suncalc = SunCalc()
    pos = suncalc.get_position(date, lat, lng)
    assert np.isclose(pos['azimuth'], -2.5003175907168385)
    assert np.isclose(pos['altitude'], -0.7000406838781611)


def test_get_times():
    """getTimes returns sun phases for the given date and location
    """
    suncalc = SunCalc()
    times = suncalc.get_times(date, lat, lng)
    for key, value in testTimes.items():
        assert times[key].strftime("%Y-%m-%dT%H:%M:%SZ") == value


def test_get_times_height():
    """getTimes adjusts sun phases when additionally given the observer height
    """
    suncalc = SunCalc()
    times = suncalc.get_times(date, lat, lng, height)
    for key, value in heightTestTimes.items():
        assert times[key].strftime("%Y-%m-%dT%H:%M:%SZ") == value


# t.test('getMoonPosition returns moon position data given time and location', function (t) {
#     var moonPos = SunCalc.getMoonPosition(date, lat, lng);
#
#     t.ok(near(moonPos.azimuth, -0.9783999522438226), 'azimuth');
#     t.ok(near(moonPos.altitude, 0.014551482243892251), 'altitude');
#     t.ok(near(moonPos.distance, 364121.37256256194), 'distance');
#     t.end();
# });
#
# t.test('getMoonIllumination returns fraction and angle of moon\'s illuminated limb and phase', function (t) {
#     var moonIllum = SunCalc.getMoonIllumination(date);
#
#     t.ok(near(moonIllum.fraction, 0.4848068202456373), 'fraction');
#     t.ok(near(moonIllum.phase, 0.7548368838538762), 'phase');
#     t.ok(near(moonIllum.angle, 1.6732942678578346), 'angle');
#     t.end();
# });
#
# t.test('getMoonTimes returns moon rise and set times', function (t) {
#     var moonTimes = SunCalc.getMoonTimes(new Date('2013-03-04UTC'), lat, lng, true);
#
#     t.equal(moonTimes.rise.toUTCString(), 'Mon, 04 Mar 2013 23:54:29 GMT');
#     t.equal(moonTimes.set.toUTCString(), 'Mon, 04 Mar 2013 07:47:58 GMT');
#
#     t.end();
# });
