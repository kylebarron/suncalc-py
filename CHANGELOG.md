# Changelog

## Unreleased

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
