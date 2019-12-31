from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized


class SuperuserAuthoriziation(Authorization):
    """
    for any action, only allow super users, optionally staff
    this does not check for any other permissions
    """

    def __init__(self, allow_staff=False, **kwargs):
        super().__init__(**kwargs)
        self.allow_staff = allow_staff

    def is_superuser(self, bundle):
        valid = bundle.request.user.is_superuser
        valid |= (self.allow_staff and bundle.request.user.is_staff)
        return valid

    def is_active(self, bundle):
        return bundle.request.user.is_active

    def is_allowed_or_raise(self, bundle):
        if self.is_superuser(bundle) and self.is_active(bundle):
            return True
        raise Unauthorized("You are not allowed to access that resource.")

    def create_detail(self, object_list, bundle):
        return self.is_allowed_or_raise(bundle)

    def read_detail(self, object_list, bundle):
        return self.is_allowed_or_raise(bundle)

    def update_detail(self, object_list, bundle):
        return self.is_allowed_or_raise(bundle)

    def delete_detail(self, object_list, bundle):
        return object_list if self.is_allowed_or_raise(bundle) else []

    def create_list(self, object_list, bundle):
        return object_list if self.is_allowed_or_raise(bundle) else []

    def read_list(self, object_list, bundle):
        return object_list if self.is_allowed_or_raise(bundle) else []

    def update_list(self, object_list, bundle):
        return object_list if self.is_allowed_or_raise(bundle) else []

    def delete_list(self, object_list, bundle):
        return object_list if self.is_allowed_or_raise(bundle) else []
