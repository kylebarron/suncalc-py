from importlib.metadata import PackageNotFoundError, version

from .suncalc import get_position, get_times

__author__ = """Kyle Barron"""
__email__ = 'kylebarron2@gmail.com'

try:
    __version__ = version('suncalc')
except PackageNotFoundError:
    __version__ = 'uninstalled'
