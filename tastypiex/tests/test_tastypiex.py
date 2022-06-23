import os

import unittest


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
