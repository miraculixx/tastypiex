from tastypie.api import Api
from tastypie.authentication import Authentication
from tastypie.resources import Resource

from unittest.mock import patch, Mock

import os

import unittest

from tastypiex.centralize import ApiCentralizer
from tastypiex.deferredauth import DeferredAuthentication


class TastypieXTestCases(unittest.TestCase):
    """ #SHAME this tests the bare minimum

    Rationale:
        We test tastypiex functionality as part of our internal applications,
        i.e. there is sufficient test coverage for our purpose
    """
    # FIXME add realtests

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

