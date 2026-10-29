# Changelog

## Unreleased

- Dates that are `NaT` now give `NaN` positions and `NaT` times. Before, `get_position` and `get_times` raised `ValueError` for `pd.NaT`, and returned results for 1677-09-21 for `NaT` in a Series, `DatetimeIndex` or array. See #19.
- `get_times` no longer emits `RuntimeWarning: invalid value encountered in arccos` when the sun doesn't reach an angle in `times` that day, like night in summer at high latitudes. As before, those times are `NaT`. Without pandas, they also no longer emit numpy 2.5's `DeprecationWarning` for generic-unit `NaT`. See #13.
- Fix `DatetimeIndex` and numpy `datetime64` input, which raised `AttributeError` after the pandas 3 resolution fix, and make every datetime64 resolution give the same result

## [0.1.3] - 2023-04-18

- Ensure pandas 2.0 compatibility (fix integer casting of datetimes)

## [0.1.2] - 2020-12-02

- Try to catch NaN before passing to `datetime.utcfromtimestamp`

## [0.1.1] - 2020-11-20

- Fix PyPI install by adding `MANIFEST.in`
- Update documentation

## [0.1.0] - 2020-11-19

- Initial release on PyPI
