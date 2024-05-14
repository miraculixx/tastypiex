from datetime import timedelta
from django.conf import settings

from django.utils import timezone
from tastypie.authentication import ApiKeyAuthentication


class RotatingApiKeyAuthentication(ApiKeyAuthentication):
    """ Provides time-limited apikeys and automated rotation

    How it works:
        1. Upon REST API access, checks validity using ApiKeyAuthentication
        2. Checks whether the key has expired v.v. the specified duration,
           expired = (api_key.created + duration) < current time
        3. If no longer valid, generates a new key and denies access

    Usage:
        # tastypie.Resource
        # -- combine with other authentication schemes
        class Meta:
            authentication = MultiAuthentication(RotatingApiKeyAuthentication(),
                                                 SessionAuthentication())

        # settings
        # -- seconds
        TASTYPIE_APIKEY_DURATION = 3600
        # -- days
        TASTYPIE_APIKEY_DURATION = dict(days=1) # calendar day
        # -- hours, or any other kwarg for timedelta()
        TASTYPIE_APIKEY_DURATION = dict(hours=24) # 24 hours
        # -- we also handle years as 52 * value
        TASTYPIE_APIKEY_DURATION = dict(years=2) # 24 hours
        # -- apikey postfix to interactively designate a key permanent
        TASTYPIE_APIKEY_PERMANENT_POSTFIX = '#p'

        Instead of settings.TASTYPIE_APIKEY_DURATION you can also specify
        RotatingApiKeyAuthentication(duration=value), which will take precedence
        over settings. This allows per-resource specifics.
    """
    _magic_postfix = '#p'

    def __init__(self, *args, duration=None, **kwargs):
        self._apikey_duration = duration
        super().__init__(*args, **kwargs)

    def get_key(self, user, api_key, now=timezone.now):
        # check the key twice
        # -- first, check the key as is
        # -- second, check the key with the magic postfix (if user does not provide)
        valid = super().get_key(user, api_key)
        valid = valid if valid is True else super().get_key(user, api_key + self._magic_postfix)
        rotated = self.maybe_rotate_key(user, now=now) if valid is True else False
        return self._unauthorized() if rotated else valid

    def maybe_rotate_key(self, user, now=timezone.now):
        # rotate the key if the current key has expired
        # return True if a new key has been generated, else False
        # usernames listed in settings.TASTYPIE_APIKEY_PERMANENT are never expired
        if (user.api_key.key.endswith(getattr(settings, 'TASTYPIE_APIKEY_PERMANENT_POSTFIX', self._magic_postfix))
                or user.username in (getattr(settings, 'TASTYPIE_APIKEY_PERMANENT', None) or [])):
            return False
        duration = getattr(settings, 'TASTYPIE_APIKEY_DURATION', self._apikey_duration)
        if duration:
            duration = duration if isinstance(duration, dict) else {'seconds': int(duration)}
            if 'years' in duration:
                duration['weeks'] = 52 * duration.pop('years')
            valid_dt = user.api_key.created + timedelta(**duration)
            expired = now() > valid_dt
            if expired:
                user.api_key.key = user.api_key.generate_key()
                user.api_key.created = timezone.now()
                user.api_key.save()
                return True
        return False


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
        seconds(
    """
    duration = duration or specs
    seconds_per_unit = {
        's': 1,
        'h': 60 * 60,
        'd': 24 * 60 * 60,
        'w': 7 * 24 * 60 * 60,
        'y': 365 * 24 * 60 * 60
    }
    if str(duration)[-1] in seconds_per_unit:
        unit = duration[-1]
        duration = int(duration[:-1]) * seconds_per_unit[unit]
    elif isinstance(duration, dict):
        duration = timedelta(**duration).total_seconds()
    else:
        duration = int(duration)
    return duration
