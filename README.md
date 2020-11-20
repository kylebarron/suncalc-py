# suncalc-py

<p>
  <a href="https://github.com/kylebarron/suncalc-py/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/kylebarron/suncalc-py/workflows/test/badge.svg" alt="Test">
  </a>
  <a href="https://pypi.org/project/suncalc" target="_blank">
      <img src="https://img.shields.io/pypi/v/suncalc?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://github.com/kylebarron/suncalc-py/blob/master/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/kylebarron/suncalc-py.svg" alt="Downloads">
  </a>
</p>


A fast, vectorized Python implementation of [`suncalc.js`][suncalc-js] for
calculating sun position and sunlight phases (times for sunrise, sunset, dusk,
etc.) for the given location and time.

[suncalc-js]: https://github.com/mourner/suncalc

While other similar libraries exist, I didn't originally encounter any that met
my requirements of being both openly-licensed and vectorized <sup>1</sup>

## Install

```
pip install suncalc
```

## Using

### Example

`suncalc` is designed to work both with single values and with arrays of values.

First, import the module:

```py
from suncalc import get_position, get_times
from datetime import datetime
```

There are currently two methods: `get_position`, to get the sun azimuth and
altitude for a given date and position, and `get_times`, to get sunlight phases
for a given date and position.

```py
date = datetime.now()
lon = 20
lat = 45
get_position(date, lon, lat)
# {'azimuth': -0.8619668996997687, 'altitude': 0.5586446727994595}

get_times(date, lon, lat)
# {'solar_noon': Timestamp('2020-11-20 08:47:08.410863770'),
#  'nadir': Timestamp('2020-11-19 20:47:08.410863770'),
#  'sunrise': Timestamp('2020-11-20 03:13:22.645455322'),
#  'sunset': Timestamp('2020-11-20 14:20:54.176272461'),
#  'sunrise_end': Timestamp('2020-11-20 03:15:48.318936035'),
#  'sunset_start': Timestamp('2020-11-20 14:18:28.502791748'),
#  'dawn': Timestamp('2020-11-20 02:50:00.045539551'),
#  'dusk': Timestamp('2020-11-20 14:44:16.776188232'),
#  'nautical_dawn': Timestamp('2020-11-20 02:23:10.019832520'),
#  'nautical_dusk': Timestamp('2020-11-20 15:11:06.801895264'),
#  'night_end': Timestamp('2020-11-20 01:56:36.144269287'),
#  'night': Timestamp('2020-11-20 15:37:40.677458252'),
#  'golden_hour_end': Timestamp('2020-11-20 03:44:46.795967773'),
#  'golden_hour': Timestamp('2020-11-20 13:49:30.025760010')}
```

These methods also work for _arrays_ of data, and since the implementation is
vectorized it's much faster than a for loop in Python.

```py
import pandas as pd

df = pd.DataFrame({
    'date': [date] * 10,
    'lon': [lon] * 10,
    'lat': [lat] * 10
})
pd.DataFrame(get_position(df['date'], df['lon'], df['lat']))
# azimuth	altitude
# 0	-1.485509	-1.048223
# 1	-1.485509	-1.048223
# ...

pd.DataFrame(get_times(df['date'], df['lon'], df['lat']))['solar_noon']
# 0   2020-11-20 08:47:08.410863872+00:00
# 1   2020-11-20 08:47:08.410863872+00:00
# ...
# Name: solar_noon, dtype: datetime64[ns, UTC]
```

If you want to join this data back to your `DataFrame`, you can use `pd.concat`:

```py
times = pd.DataFrame(get_times(df['date'], df['lon'], df['lat']))
pd.concat([df, times], axis=1)
```

### API

#### `get_position`

Calculate sun position (azimuth and altitude) for a given date and
latitude/longitude

- `date` (`datetime` or a pandas series of datetimes): date and time to find sun position of. **Datetime must be in UTC**.
- `lng` (`float` or numpy array of `float`): longitude to find sun position of
- `lat` (`float` or numpy array of `float`): latitude to find sun position of

Returns a `dict` with two keys: `azimuth` and `altitude`. If the input values
were singletons, the `dict`'s values will be floats. Otherwise they'll be numpy
arrays of floats.

#### `get_times`

- `date` (`datetime` or a pandas series of datetimes): date and time to find sunlight phases of. **Datetime must be in UTC**.
- `lng` (`float` or numpy array of `float`): longitude to find sunlight phases of
- `lat` (`float` or numpy array of `float`): latitude to find sunlight phases of
- `height` (`float` or numpy array of `float`, default `0`): observer height in meters
- `times` (`Iterable[Tuple[float, str, str]]`): an iterable defining the angle above the horizon and strings for custom sunlight phases. The default is:

    ```py
    # (angle, morning name, evening name)
    DEFAULT_TIMES = [
        (-0.833, 'sunrise', 'sunset'),
        (-0.3, 'sunrise_end', 'sunset_start'),
        (-6, 'dawn', 'dusk'),
        (-12, 'nautical_dawn', 'nautical_dusk'),
        (-18, 'night_end', 'night'),
        (6, 'golden_hour_end', 'golden_hour')
    ]
    ```

Returns a `dict` where the keys are `solar_noon`, `nadir`, plus any keys passed
in the `times` argument. If the input values were singletons, the `dict`'s
values will be of type `datetime.datetime` (or `pd.Timestamp` if you have pandas
installed, which is a subclass of and therefore compatible with
`datetime.datetime`). Otherwise they'll be pandas `DateTime` series. **The
returned times will be in UTC.**

## Benchmark

This benchmark is to show that the vectorized implementation is nearly 100x
faster than a for loop in Python.

First set up a `DataFrame` with random data. Here I create 100,000 rows.

```py
from suncalc import get_position, get_times
import pandas as pd

def random_dates(start, end, n=10):
    """Create an array of random dates"""
    start_u = start.value//10**9
    end_u = end.value//10**9
    return pd.to_datetime(np.random.randint(start_u, end_u, n), unit='s')

start = pd.to_datetime('2015-01-01')
end = pd.to_datetime('2018-01-01')
dates = random_dates(start, end, n=100_000)

lons = np.random.uniform(low=-179, high=179, size=(100_000,))
lats = np.random.uniform(low=-89, high=89, size=(100_000,))

df = pd.DataFrame({'date': dates, 'lat': lats, 'lon': lons})
```

Then compute `SunCalc.get_position` two ways: the first using the vectorized
implementation and the second using `df.apply`, which is equivalent to a for
loop. The first is more than **100x faster** than the second.

```py
%timeit get_position(df['date'], df['lon'], df['lat'])
# 41.4 ms ± 437 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

%timeit df.apply(lambda row: get_position(row['date'], row['lon'], row['lat']), axis=1)
# 4.89 s ± 184 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

Likewise, compute `SunCalc.get_times` the same two ways: first using the
vectorized implementation and the second using `df.apply`. The first is **2800x
faster** than the second! Some of the difference here is that under the hood the
non-vectorized approach uses `pd.to_datetime` while the vectorized
implementation uses `np.astype('datetime64[ns, UTC]')`. `pd.to_datetime` is
really slow!!

```py
%timeit get_times(df['date'], df['lon'], df['lat'])
# 55.3 ms ± 1.91 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)

%time df.apply(lambda row: get_times(row['date'], row['lon'], row['lat']), axis=1)
# CPU times: user 2min 33s, sys: 288 ms, total: 2min 34s
# Wall time: 2min 34s
```

---

1: [`pyorbital`](https://github.com/pytroll/pyorbital) looks great but is
GPL3-licensed; [`pysolar`](https://github.com/pingswept/pysolar) is also
GPL3-licensed; [`pyEphem`](https://rhodesmill.org/pyephem/) is LGPL3-licensed.
[`suncalcPy`](https://github.com/Broham/suncalcPy) is another port of
`suncalc.js`, and is MIT-licensed, but doesn't use Numpy and thus isn't
vectorized. I recently discovered [`sunpy`](https://github.com/sunpy/sunpy) and
[`astropy`](https://github.com/astropy/astropy), both of which probably would've
worked but I didn't see them at first and they look quite complex for this
simple task...
