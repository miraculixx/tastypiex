import six
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypiex.util import load_class


class DeferredAuthentication(Authentication):
    """
    instantiate the authentication class at runtime instead
    of at load time. with this, client applications can
    define their own loaders without changing the actual
    API, and they can also define chains of authentication
    backends.

    Use:
        class SomeResource(Resource):
            authentication = DeferredAuthentication('SOME_SETTING')

        settings.py:
            SOME_SETTING = ('path.to.backend', ...)

        Every backend should needs at least an is_authenticated method.
        It can be derived from tastypie.Authentication or from object, i.e.
        you don't need a dependency to tastypie to make use of it.
    """

    def __init__(self, setting=None,
                 default_backend=None,
                 require_active=True):
        self.setting = setting
        self.default_backend = default_backend or ('tastypie.authentication.Authentication',)
        self._backends = None

    def load_backends(self):
        from django.conf import settings
        backends = getattr(settings, self.setting, self.default_backend)
        if isinstance(backends, six.string_types):
            backends = (backends,)
        for backend_name in backends:
            backend = load_class(backend_name)()
            self._backends.append(backend)
        return self._backends

    @property
    def backends(self):
        return self._backends or self.load_backends()

    def is_authenticated(self, request, **kwargs):
        for backend in self.backends:
            result = backend.is_authenticated(request, **kwargs)
            if result:
                return result
        return False

    def get_identifier(self, request):
        for backend in self.backends:
            if hasattr(backend, 'get_identifier'):
                result = backend.get_identifier(request)
                if result:
                    return result
        return super(DeferredAuthentication, self).get_identifier(request)

    def check_active(self, user):
        for backend in self.backends:
            if hasattr(backend, 'check_active'):
                result = backend.check_active(user)
                if result:
                    return result
        return super(DeferredAuthentication, self).check_active(user)


class DeferredAuthorization(Authorization):
    """
    instantiate the authorization class at runtime instead
    of at load time. with this, client applications can
    define their own loaders without changing the actual
    API, and they can also define chains of authorization
    backends.

    Use:
        class SomeResource(Resource):
            authorization = DeferredAuthorization('SOME_SETTING')

        settings.py:
            SOME_SETTING = ('path.to.backend', ...)

        Define those methods that you require, out of
    """

    def __init__(self, setting=None,
                 default_backend=None,
                 require_active=True):
        self.setting = setting
        self.default_backend = default_backend or ('tastypie.authorization.Authorization')
        self._backends = None

    def load_backends(self):
        from django.conf import settings
        backends = getattr(settings, self.setting, self.default_backend)
        if isinstance(backends, six.string_types):
            backends = (backends,)
        for backend_name in backends:
            backend = load_class(backend_name)()
            self._backends.append(backend)
        return self._backends

    @property
    def backends(self):
        return self._backends or self.load_backends()

    def _check_method(method):  # @NoSelf
        """
        generate methods as defined below
        """

        def inner(self, request, object_list):
            for backend in self.backends:
                method = getattr(backend, method)
                result = method(request, object_list)
                if result:
                    return result

        inner.__doc__ = "{}".format(getattr(Authorization, method).__doc__)
        return inner

    apply_limits = _check_method('apply_limits')
    create_detail = _check_method('create_detail')
    create_list = _check_method('create_list')
    delete_detail = _check_method('delete_detail')
    delete_list = _check_method('delete_list')
    read_detail = _check_method('read_detail')
    read_list = _check_method('read_list')
    update_detail = _check_method('update_detail')
    update_list = _check_method('update_list')
