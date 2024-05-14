from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from tastypie.api import Api
from tastypie.authentication import Authentication
from tastypie.http import HttpUnauthorized
from tastypie.resources import Resource

from unittest.mock import patch, Mock

import os
from django.test import TestCase

from tastypiex.centralize import ApiCentralizer
from tastypiex.deferredauth import DeferredAuthentication
from tastypiex.rotapikey import seconds


class TastypieXTestCases(TestCase):
    """ #SHAME this tests the bare minimum

    Rationale:
        We test tastypiex functionality as part of our internal applications,
        i.e. there is sufficient test coverage for our purpose
    """

    # FIXME add realtests

    def setUp(self):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'example.settings'

    def test_simple(self):
        from tastypiex import centralize
        from tastypiex import cleanfields
        from tastypiex import modresource
        from tastypiex import requestqs
        from tastypiex import requesttrace
        from tastypiex import util
        centralize = centralize
        cleanfields = cleanfields
        modresource = modresource
        requestqs = requestqs
        requesttrace = requesttrace
        util = util

    def test_django_dependencies(self):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'app.settings'
        from tastypiex import cors
        from tastypiex import cqrsmixin
        from tastypiex import deferredauth
        from tastypiex import fromfield
        from tastypiex import reasonableauth
        from tastypiex import selfauth
        from tastypiex import superuserauth
        cors = cors
        cqrsmixin = cqrsmixin
        deferredauth = deferredauth
        fromfield = fromfield
        reasonableauth = reasonableauth
        selfauth = selfauth
        superuserauth = superuserauth

    def test_deferred_auth(self):
        settings = object()
        request = Mock()
        with patch('django.conf.settings') as settings:
            settings.SOME_AUTH = 'tastypie.authentication.Authentication'
            auth = DeferredAuthentication('SOME_AUTH')
            authenticated = auth.is_authenticated(request)
            self.assertTrue(authenticated)

    def test_centralize_override_authentication(self):
        """ test tastypiex.ApiCentralizer overrides all resources Meta.authentication """

        class FooResource(Resource):
            class Meta:
                authentication = Authentication()

        class BarResource(Resource):
            class Meta:
                authentication = Authentication()

        class MyAuthentication(Authentication):
            pass

        class CustomMeta:
            authentication = MyAuthentication()

        fooresource = FooResource()
        barresource = BarResource()
        v1_api = Api('v1')
        v1_api.register(fooresource)
        v1_api.register(barresource)
        centralizer = ApiCentralizer(apis=[v1_api], autoinit=False)
        centralizer.centralize(centralizer.apis, meta=CustomMeta)
        self.assertIsInstance(fooresource._meta.authentication, MyAuthentication)
        self.assertIsInstance(barresource._meta.authentication, MyAuthentication)

    def test_rotating_apikey_timedelta(self):
        # test rotating apikey with timedelta duration
        # -- e.g. TASTYPIE_APIKEY_DURATION = dict(days=5)
        from tastypie.models import ApiKey
        from tastypiex.rotapikey import RotatingApiKeyAuthentication
        user = User.objects.create_user('testuser')
        apikey, created = ApiKey.objects.get_or_create(user=user)
        current_key = apikey.key
        auth = RotatingApiKeyAuthentication()
        # no limitation
        future_dt = lambda: timezone.now() + timedelta(weeks=52 * 5)
        self.assertTrue(auth.get_key(user, current_key))
        self.assertTrue(auth.get_key(user, current_key, now=future_dt))
        # limit to some duration
        with self.settings(TASTYPIE_APIKEY_DURATION={'days': 5}):
            # -- still valid within time period
            future_dt = lambda: apikey.created + timedelta(days=4)
            self.assertTrue(auth.get_key(user, current_key, now=future_dt))
            # -- not valid after time period
            future_dt = lambda: apikey.created + timedelta(days=6)
            self.assertIsInstance(auth.get_key(user, current_key, now=future_dt), HttpUnauthorized)
            # -- new key has been generated
            new_key = user.api_key.key
            self.assertNotEqual(current_key, new_key)

    def test_rotating_apikey_seconds(self):
        # test rotating apikey with seconds duration
        # -- e.g. TASTYPIE_APIKEY_DURATION = seconds('5d')
        from tastypie.models import ApiKey
        from tastypiex.rotapikey import RotatingApiKeyAuthentication
        user = User.objects.create_user('testuser')
        apikey, created = ApiKey.objects.get_or_create(user=user)
        current_key = apikey.key
        auth = RotatingApiKeyAuthentication()
        # no limitation
        future_dt = lambda: timezone.now() + timedelta(weeks=52 * 5)
        self.assertTrue(auth.get_key(user, current_key))
        self.assertTrue(auth.get_key(user, current_key, now=future_dt))
        # limit to some duration
        with self.settings(TASTYPIE_APIKEY_DURATION=seconds('5d')):
            # -- still valid within time period
            future_dt = lambda: apikey.created + timedelta(days=4)
            self.assertTrue(auth.get_key(user, current_key, now=future_dt))
            # -- not valid after time period
            future_dt = lambda: apikey.created + timedelta(days=6)
            self.assertIsInstance(auth.get_key(user, current_key, now=future_dt), HttpUnauthorized)
            # -- new key has been generated
            new_key = user.api_key.key
            self.assertNotEqual(current_key, new_key)

    def test_no_rotating_apikey_permanent_settings(self):
        # test user exemption from apikey rotation, using settings.TASTYPIE_APIKEY_PERMANENT
        # -- this verifies that a user's key is never rotated if the user is in TASTYPIE_APIKEY_PERMANENT
        from tastypie.models import ApiKey
        from tastypiex.rotapikey import RotatingApiKeyAuthentication
        user = User.objects.create_user('testuser')
        apikey, created = ApiKey.objects.get_or_create(user=user)
        current_key = apikey.key
        auth = RotatingApiKeyAuthentication()
        # no limitation
        future_dt = lambda: timezone.now() + timedelta(weeks=52 * 5)
        self.assertTrue(auth.get_key(user, current_key))
        self.assertTrue(auth.get_key(user, current_key, now=future_dt))
        # test user exemption from apikey rotation
        with self.settings(TASTYPIE_APIKEY_DURATION={'days': 5},
                           TASTYPIE_APIKEY_PERMANENT=[user.username]):
            # -- still valid within time period
            future_dt = lambda: apikey.created + timedelta(days=4)
            self.assertTrue(auth.get_key(user, current_key, now=future_dt))
            # -- still valid after time period
            future_dt = lambda: apikey.created + timedelta(days=6)
            self.assertEqual(auth.get_key(user, current_key, now=future_dt), True)
            # -- no new key has been generated
            new_key = user.api_key.key
            self.assertEqual(current_key, new_key)

    def test_no_rotating_apikey_permanent_magic(self):
        # test user exemption from apikey rotation, using magic postfix
        # -- this verifies that a key with the magic postfix (#p) is never rotated
        from tastypie.models import ApiKey
        from tastypiex.rotapikey import RotatingApiKeyAuthentication
        user = User.objects.create_user('testuser')
        apikey, created = ApiKey.objects.get_or_create(user=user)
        current_key = apikey.key
        # add magic postfix
        apikey.key = apikey.key + RotatingApiKeyAuthentication._magic_postfix
        apikey.save()
        user.refresh_from_db()
        auth = RotatingApiKeyAuthentication()
        # no limitation
        future_dt = lambda: timezone.now() + timedelta(weeks=52 * 5)
        self.assertTrue(auth.get_key(user, current_key))
        self.assertTrue(auth.get_key(user, current_key, now=future_dt))
        # test user exemption from apikey rotation
        with self.settings(TASTYPIE_APIKEY_DURATION={'days': 5}):
            # -- still valid within time period
            future_dt = lambda: apikey.created + timedelta(days=4)
            self.assertTrue(auth.get_key(user, current_key, now=future_dt))
            # -- still valid after time period
            future_dt = lambda: apikey.created + timedelta(days=6)
            self.assertEqual(auth.get_key(user, current_key, now=future_dt), True)
            # also pass including magic postfix
            self.assertTrue(auth.get_key(user, current_key + RotatingApiKeyAuthentication._magic_postfix,
                                         now=future_dt))
            # -- no new key has been generated
            user.refresh_from_db()
            new_key = user.api_key.key.replace(RotatingApiKeyAuthentication._magic_postfix, '')
            self.assertEqual(current_key, new_key)

    def test_duration_as_seconds(self):
        self.assertEqual(seconds('1s'), 1)
        self.assertEqual(seconds('500s'), 500)
        self.assertEqual(seconds('5h'), timedelta(hours=5).total_seconds())
        self.assertEqual(seconds('1d'), timedelta(days=1).total_seconds())
        self.assertEqual(seconds('1w'), timedelta(days=7).total_seconds())
        self.assertEqual(seconds('5w'), timedelta(days=7 * 5).total_seconds())
        self.assertEqual(seconds('1y'), timedelta(days=365).total_seconds())
        self.assertEqual(seconds(hours=5), timedelta(hours=5).total_seconds())
        self.assertEqual(seconds(days=365), timedelta(days=365).total_seconds())






