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


    def test_rotating_apikey(self):
        from tastypie.models import ApiKey
        from tastypiex.rotapikey import RotatingApiKeyAuthentication
        user = User.objects.create_user('testuser')
        apikey = ApiKey.objects.create(user=user)
        current_key = apikey.key
        auth = RotatingApiKeyAuthentication()
        # no limitation
        future_dt = lambda : timezone.now() + timedelta(weeks=52*5)
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
