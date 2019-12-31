from django.contrib.auth.models import User
from tastypie.exceptions import Unauthorized

from tastypiex.reasonableauth import ReasonableDjangoAuthorization


class SelfUpdateAuthorization(ReasonableDjangoAuthorization):
    """
    update and delete allowed if resource object belongs to user
    or if current user.is_superuser. User must also be active
    """

    def is_superuser(self, bundle):
        return bundle.request.user.is_superuser

    def is_active(self, bundle):
        return bundle.request.user.is_active

    def check_detail_perm(self, object_list, bundle):
        if self.is_active(bundle):
            # user must be owner of the object or superuser
            if isinstance(bundle.obj, User):
                allowed = bundle.obj == bundle.request.user
            elif hasattr(bundle.obj, 'user'):
                allowed = bundle.obj.user == bundle.request.user
            else:
                allowed = False
            allowed |= self.is_superuser(bundle)
            if allowed:
                return True
        raise Unauthorized("You are not allowed to access that resource.")

    def read_detail(self, object_list, bundle):
        # we need read access to update or delete
        return self.check_detail_perm(object_list, bundle)

    def update_detail(self, object_list, bundle):
        return self.check_detail_perm(object_list, bundle)

    def delete_detail(self, object_list, bundle):
        return self.check_detail_perm(object_list, bundle)
