from tastypie.exceptions import ImmediateHttpResponse, Unauthorized
from tastypie.http import HttpUnauthorized
from tastypie.utils import trailing_slash


class CQRSApiMixin(object):
    """
    A mixin to add CQRS-style commands to URL resources

    Usage:

        class FooResource(CQRSApiMixin, Resource):
            class Meta:
               resource_name = 'foo'

            @cqrsapi
            def xyz(bundle, *args, **kwargs):
                ....
                return self.create_response(request, data)

        This will add url /api/foo/<pk>/xyz/
    """

    def prepend_urls(self):
        """
        prepend command urls as <resource_name>/<uri>/<command>
        """
        from django.urls import re_path as urlfn

        urls = super(CQRSApiMixin, self).prepend_urls()
        if not hasattr(self._meta, 'extra_actions'):
            self._meta.extra_actions = []
        for name, method in self.__class__.__dict__.items():
            if not hasattr(method, 'cqrsapi'):
                continue
            # link meta information
            cqrsname = method.cqrsname or name
            if method.allowed_methods is None:
                method.allowed_methods = self._meta.allowed_methods
            # add url
            # adopted from tastypie.Resource.base_urls
            pattern = r"^(?P<resource_name>%s)/(?P<%s>.*?)/(?P<command>%s)%s$"
            args = (self._meta.resource_name, self._meta.detail_uri_name,
                    cqrsname, trailing_slash())
            view = self.wrap_view(name)
            url = urlfn(pattern % args, view,
                        name="api_dispatch_command_%s" % cqrsname)
            urls.append(url)
            # add to extra actions (used in django-tastypie-swagger)
            for http_method in method.allowed_methods:
                action = {
                    'name': cqrsname,
                    'summary': "{} a {}".format(cqrsname, self._meta.resource_name),
                    'notes': method.__doc__,
                    'response_class': self.__class__,
                    'http_method': http_method,
                }
                self._meta.extra_actions.append(action)
        return urls


def cqrsapi(method=None, name=None, allowed_methods=None, authenticate=True, permission=True):
    cqrsargs = dict(cqrsargs=dict(cqrs_method=method,
                                  cqrs_name=name,
                                  allowed_methods=allowed_methods,
                                  permission=permission,
                                  authenticate=authenticate))

    def wrap(method):
        # wrap() is called at declaration time and returns dispatch
        # dispatch() is the actual view function, effectively overriding Resource.dispatch
        def dispatch(self, request, *args, **kwargs):
            # this adopted from standard tastypie in Resource.dispatch()
            # -- main difference here is that we call the @cqrsapi'd method()
            def inner_dispatch(request, *args, **kwargs):
                self.method_check(request, allowed=dispatch.allowed_methods)
                if authenticate:
                    self.is_authenticated(request)
                if permission and self._meta.authorization:
                    bundle = self.build_bundle(request=request)
                    if any(hasattr(auth, 'is_authorized') for auth in (self, self._meta.authorization)):
                        # use Resource.is_authorized, or Resource.Meta.authorization.is_authorized, if available
                        # -- is_authorized() is the generic method for permission authorization
                        # -- we can pass it the cqrsname as the action
                        auth_meth = getattr(self, 'is_authorized', None) or getattr(self._meta.authorization,
                                                                                    'is_authorized')
                        auth_args = dispatch.cqrsname, [request.path], bundle
                    else:
                        # fall back to standard authorization, using read_list or create_list
                        # -- standard authorization primitives are of the format <crud>_<list|detail>
                        #    e.g. read_list, create_list, read_detail, create_detail, etc.
                        # -- use the request method to derive the action, we simply use the list variant
                        authorization = self._meta.authorization
                        action = 'read' if request.method in ('GET', 'HEAD', 'OPTIONS') else 'create'
                        auth_meth = getattr(authorization, f'{action}_list')
                        auth_args = [request.path], bundle
                    try:
                        auth_meth(*auth_args)
                    except Unauthorized as e:
                        raise ImmediateHttpResponse(HttpUnauthorized())
                self.throttle_check(request)
                resp = method(self, request, *args, **kwargs)
                self.log_throttled_access(request)
                return resp

            # setup hooks
            noop = lambda *args, **kwargs: None  # noqa
            pre_dispatch = getattr(self, 'pre_cqrs_dispatch', noop)
            real_dispatch = getattr(self, 'cqrs_dispatch', inner_dispatch)
            post_dispatch = getattr(self, 'post_cqrs_dispatch', noop)
            # do actual dispatching
            pre_dispatch(request, *args, **kwargs, **cqrsargs)
            resp = real_dispatch(request, *args, **kwargs, **cqrsargs)
            post_dispatch(resp, *args, **kwargs, **cqrsargs)
            return resp

        dispatch.cqrsname = name or method.__name__
        dispatch.allowed_methods = allowed_methods
        dispatch.permission = permission if isinstance(permission, str) else None
        dispatch.cqrsapi = True
        dispatch.__doc__ = method.__doc__
        return dispatch

    if callable(method):
        return wrap(method)
    return wrap
