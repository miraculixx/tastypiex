from django.contrib.auth.models import User
from tastypie.exceptions import Unauthorized

from tastypiex.reasonableauth import ReasonableDjangoAuthorization


class SelfUpdateAuthorization(ReasonableDjangoAuthorization):
    """
    update and delete allowed if resource object belongs to user
    or if current user.is_superuser/is_staff.

    User must also be active
    """

    def __init__(self, allow_staff=True, **kwargs):
        super().__init__(**kwargs)
        self.allow_staff = allow_staff

    def is_superuser(self, bundle):
        valid = bundle.request.user.is_superuser
        valid |= (self.allow_staff and bundle.request.user.is_staff)
        return valid

    def is_active(self, bundle):
        return bundle.request.user.is_active

    def check_obj_perm(self, obj, bundle):
        # user must be owner of the object or superuser
        if isinstance(obj, User):
            allowed = obj == bundle.request.user
        elif hasattr(obj, 'user'):
            allowed = obj.user == bundle.request.user
        else:
            allowed = False
        allowed |= self.is_superuser(bundle)
        if allowed:
            return True
        return False

    def check_perm(self, action, object_list, bundle):
        # reduce list of objects to those allowed for user
        if self.is_active(bundle):
            objects_to_check = (object_list if action == 'list' else [bundle.obj])
            filtered = [obj for obj in objects_to_check if self.check_obj_perm(obj, bundle)]
            if filtered:
                return filtered if action == 'list' else True
        raise Unauthorized("You are not allowed to access that resource.")

    def read_list(self, object_list, bundle):
        return object_list if self.check_perm('list', object_list, bundle) else []

    def update_list(self, object_list, bundle):
        return object_list if self.check_perm('list', object_list, bundle) else []

    def delete_list(self, object_list, bundle):
        return object_list if self.check_perm('list', object_list, bundle) else []

    def read_detail(self, object_list, bundle):
        # we need read access to update or delete
        return self.check_perm('detail', object_list, bundle)

    def update_detail(self, object_list, bundle):
        return self.check_perm('detail', object_list, bundle)

    def delete_detail(self, object_list, bundle):
        return self.check_perm('detail', object_list, bundle)
