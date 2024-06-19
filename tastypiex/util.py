from importlib import import_module

import functools
import importlib
import sys
from datetime import timedelta


def load_api(qualif):
    """
    load Api instances from a string spec module.attr

    # module path.to.module.api.py
    api_v1 = Api(...)
    ...
    # somewhere
    load_api('path.to.module.api.api_v1')
    """
    parts = qualif.split('.')
    modname, apiattr = '.'.join(parts[0:-1]), parts[-1]
    try:
        if modname in sys.modules:
            mod = sys.modules.get(modname)
        else:
            mod = import_module(modname)
        api = getattr(mod, apiattr)
    except AttributeError as e:
        raise AttributeError('Cannot load api from %s, due to %s' %
                             (modname, e))
    return api


def load_class(requested_class):
    """
    Check if requested_class is a string, if so attempt to load
    class from module, otherwise return requested_class as is
    """
    if isinstance(requested_class, str):
        module_name, class_name = requested_class.rsplit(".", 1)
        try:
            m = importlib.import_module(module_name)
            return getattr(m, class_name)
        except Exception:
            raise
    return requested_class


# dicts must be hashable to be memoized
# -- see https://stackoverflow.com/a/8706053/890242
@functools.cache(lambda duration: frozenset(duration) if isinstance(duration, dict) else duration)
def seconds(duration=None, **specs):
    """ Helper to convert any duration to seconds

    Args:
        duration (str|int|dict): duration in seconds, or as timedelta kwarg
        **specs (kwargs): timedelta kwargs, optional

    Usage:
        from tastypiex.rotapikey import duration_as_seconds

        seconds('1s') == seconds(1)
        seconds('1d')
        seconds('1w')
        seconds('1y')

    Notes:
        - if duration is a dict, it is passed to timedelta()
        - if duration is a string, it is parsed as int or timedelta kwarg
        - if duration is an int, it is returned as is
        - this function is memoized to speed up repeated calls on the same input
    """
    if isinstance(duration, (int, float)):
        return duration
    duration = duration or specs
    seconds_per_unit = {
        's': 1,
        'h': 60 * 60,
        'd': 24 * 60 * 60,
        'w': 7 * 24 * 60 * 60,
        'y': 365 * 24 * 60 * 60
    }
    if isinstance(duration, dict):
        duration = timedelta(**duration).total_seconds()
    elif str(duration)[-1] in seconds_per_unit:
        unit = duration[-1]
        duration = int(duration[:-1]) * seconds_per_unit[unit]
    elif isinstance(duration, str) and duration.isdigit():
        duration = int(duration)
    else:
        duration = 0
    return duration
