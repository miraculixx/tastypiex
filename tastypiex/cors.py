'''
Add CORS headers for tastypie APIs

DEPRECATED - use django-cors-middleware instead, see Conf_DjangoCorsMiddleware

Usage:
   class MyModelResource(CORSModelResource):
       ...

   class MyResource(CORSResource):
       ...

Authors:
   original source by http://codeispoetry.me/index.php/make-your-django-tastypie-api-cross-domain/
   extensions by @miraculixx
   * deal with ?format requests
   * always return CORS headers, even if always_return_data is False
   * handle exceptions properly (e.g. raise tastypie.BadRequests)
   * provide two distinct classes for ModelResource and Resource classes

@author: patrick
'''
import logging
import warnings

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from tastypie import http
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.resources import Resource, ModelResource

logger = logging.getLogger(__name__)


class CORSResourceMixin(object):
    """
    Class implementing CORS
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "CORSResourceMixin is deprecated - use django-cors-middleware",
            DeprecationWarning)
        return super(CORSResourceMixin, self).__init__(*args, **kwargs)

    def error_response(self, *args, **kwargs):
        response = super(CORSResourceMixin, self).error_response(
            *args, **kwargs)
        return self.add_cors_headers(response, expose_headers=True)

    def add_cors_headers(self, response, expose_headers=False):
        response['Access-Control-Allow-Origin'] = '*'
        response[
            'Access-Control-Allow-Headers'] = 'content-type, authorization'
        if expose_headers:
            response['Access-Control-Expose-Headers'] = 'Location'
        return response

    def create_response(self, *args, **kwargs):
        """
        Create the response for a resource. Note this will only
        be called on a GET, POST, PUT request if
        always_return_data is True
        """
        response = super(CORSResourceMixin, self).create_response(
            *args, **kwargs)
        return self.add_cors_headers(response)

    def post_list(self, request, **kwargs):
        """
        In case of POST make sure we return the Access-Control-Allow Origin
        regardless of returning data
        """
        # logger.debug("post list %s\n%s" % (request, kwargs));
        response = super(CORSResourceMixin, self).post_list(request, **kwargs)
        return self.add_cors_headers(response, True)

    def post_detail(self, request, **kwargs):
        """
        In case of POST make sure we return the Access-Control-Allow Origin
        regardless of returning data
        """
        # logger.debug("post detail %s\n%s" (request, **kwargs));
        response = super(CORSResourceMixin, self).post_list(request, **kwargs)
        return self.add_cors_headers(response, True)

    def put_list(self, request, **kwargs):
        """
        In case of PUT make sure we return the Access-Control-Allow Origin
        regardless of returning data
        """
        response = super(CORSResourceMixin, self).put_list(request, **kwargs)
        return self.add_cors_headers(response, True)

    def put_detail(self, request, **kwargs):
        response = super(CORSResourceMixin, self).put_detail(request, **kwargs)
        return self.add_cors_headers(response, True)

    def patch_list(self, request, **kwargs):
        """
        In case of PATCH make sure we return the Access-Control-Allow Origin
        regardless of returning data
        """
        response = super(CORSResourceMixin, self).patch_list(request, **kwargs)
        return self.add_cors_headers(response, True)

    def patch_detail(self, request, **kwargs):
        response = super(CORSResourceMixin, self).patch_detail(
            request, **kwargs)
        return self.add_cors_headers(response, True)

    def delete_detail(self, request, **kwargs):
        response = super(CORSResourceMixin, self).delete_detail(
            request, **kwargs)
        return self.add_cors_headers(response, True)

    def delete_list(self, request, **kwargs):
        response = super(CORSResourceMixin, self).delete_list(
            request, **kwargs)
        return self.add_cors_headers(response, True)

    def method_check(self, request, allowed=None):
        """
        Check for an OPTIONS request. If so return the Allow- headers
        """
        if allowed is None:
            allowed = []

        request_method = request.method.lower()
        allows = ','.join(map(lambda s: s.upper(), allowed))

        if request_method == 'options':
            response = HttpResponse(allows)
            response['Access-Control-Allow-Origin'] = '*'
            response[
                'Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response[
                'Access-Control-Allow-Methods'] = "GET, PUT, POST, PATCH, DELETE"
            response['Allow'] = allows
            raise ImmediateHttpResponse(response=response)

        if request_method not in allowed:
            response = http.HttpMethodNotAllowed(allows)
            response['Allow'] = allows
            raise ImmediateHttpResponse(response=response)

        return request_method

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            request.format = kwargs.pop('format', None)
            wrapped_view = super(CORSResourceMixin, self).wrap_view(view)
            return wrapped_view(request, *args, **kwargs)

        return wrapper


# Base Extended Abstract Model


class CORSModelResource(CORSResourceMixin, ModelResource):
    pass


class CORSResource(CORSResourceMixin, Resource):
    pass


# backwards compability
BaseCorsResourceMixin = CORSResourceMixin


def corsify(cls):
    """
    CORSify an arbitrary Resource

    Add CORS headers to a resource without creating a class. This
    is useful if you can't change the Resource, e.g. because it is
    in a package that you want to reuse.

    Usage:
       class SomeResource(Resource):
          ...

       CorsifiedResource = corsify(SomeResource)
       # CorsifiedResource can be used in an API as would SomeResource, e.g.
       api = Api('v1')
       api.register(CorsifiedResource())
    """
    return type('Cors%s' % cls.__name__, (CORSResourceMixin, cls), {})
