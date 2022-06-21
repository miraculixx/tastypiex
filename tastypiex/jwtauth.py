from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
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
        from jwt_auth import mixins
        token = mixins.get_token_from_request(request)
        payload = mixins.get_payload_from_token(token)
        userid = mixins.jwt_get_user_id_from_payload(payload)
        return userid, payload

    def is_authenticated(self, request, **kwargs):
        """
        Finds the user and checks their API key.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        from jwt_auth.exceptions import AuthenticationFailed

        # validate credentials in jwt
        try:
            userid, payload = self.extract_credentials(request)
        except AuthenticationFailed:
            return self._unauthorized()
        if not userid or not payload:
            return self._unauthorized()
        return True


def jwt_get_user_id_from_payload_handler(payload):
    from jwt_auth.exceptions import AuthenticationFailed

    # this retrieves the userid from a username, not the userid
    # adapted from jwt_auth.utils.jwt_get_user_id_from_payload_handler
    username = payload.get(getattr(settings, 'JWT_PAYLOAD_USERNAME_KEY', 'username'))
    username_field = get_username_field()
    lookup_kwargs = {username_field: username}
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(**lookup_kwargs)
    except UserModel.DoesNotExist:
        user = None
    if user is None or not user.is_active:
        raise AuthenticationFailed(_("Invalid payload"))
    return user.pk
