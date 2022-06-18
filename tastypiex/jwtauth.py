from django.contrib.auth import get_user_model
from jwt_auth import mixins
from jwt_auth.exceptions import AuthenticationFailed
from tastypie.authentication import Authentication
from tastypie.compat import get_username_field
from tastypie.http import HttpUnauthorized


class JWTAuthentication(Authentication):
    """ Handles JWT auth for Tastypie, in which a user provides a valid JWT token

    Usage::

        class SomeResource(Resource):
                class Meta:
                    authentication = JWTAuthentication()

    See Also
        - backend https://github.com/webstack/django-jwt-auth
    """
    auth_type = 'bearer'

    def _unauthorized(self):
        return HttpUnauthorized()

    def extract_credentials(self, request):
        token = mixins.get_token_from_request(request)
        payload = mixins.get_payload_from_token(token)
        username = mixins.get_user_id_from_payload(payload)
        return username, payload

    def is_authenticated(self, request, **kwargs):
        """
        Finds the user and checks their API key.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        # validate credentials in jwt
        try:
            username, payload = self.extract_credentials(request)
        except AuthenticationFailed:
            return self._unauthorized()
        if not username or not payload:
            return self._unauthorized()
        # see if we can find user
        username_field = get_username_field()
        User = get_user_model()
        lookup_kwargs = {username_field: username}
        try:
            user = User.objects.get(**lookup_kwargs)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return self._unauthorized()
        # validate the user is active
        if not self.check_active(user):
            return False
        return True
