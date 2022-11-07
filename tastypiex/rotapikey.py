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
        class Meta:
            authentication = RotatingApiKeyAuthentication()

        # settings
        # -- days
        TASTYPIE_APIKEY_DURATION = 5
        # -- hours, or any other kwarg for timedelta()
        TASTYPIE_APIKEY_DURATION = dict(hours=24) # 24 hours
        # -- we also handle years as 52 * value
        TASTYPIE_APIKEY_DURATION = dict(years=2) # 24 hours

        Instead of settings.TASTYPIE_APIKEY_DURATION you can also specify
        RotatingApiKeyAuthentication(duration=value), which will take precedence
        over settings. This allows per-resource specifics.
    """
    def __init__(self, *args, duration=None, **kwargs):
        self._apikey_duration = duration
        super().__init__(*args, **kwargs)

    def get_key(self, user, api_key, now=timezone.now):
        valid = super().get_key(user, api_key)
        rotated = self.maybe_rotate_key(user, now=now) if valid is True else False
        return self._unauthorized() if rotated else valid

    def maybe_rotate_key(self, user, now=timezone.now):
        # rotate the key if the current key has expired
        # return True if a new key has been generated, else False
        duration = self._apikey_duration or getattr(settings, 'TASTYPIE_APIKEY_DURATION', None)
        if duration:
            duration = duration if isinstance(duration, dict) else {'days': int(duration)}
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
