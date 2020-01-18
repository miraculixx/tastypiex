from django.contrib.auth.models import User
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.compat import get_module_name
from tastypie.exceptions import Unauthorized

from tastypiex.reasonableauth import ReasonableDjangoAuthorization


class SelfAuthorization(Authorization):
    """
    update and delete allowed if resource object belongs to user

    If current user.is_superuser/is_staff the action is also allowed.
    Further, User must also be active.

    By default SelfAuthorization checks the Resource itself as well as
    the 'user' attribute, if there is any.

    Args:
        allow_staff (bool): if True allows staff and super users, if False
             only super users, defaults to True
        actions (str): specify the crud actions as a string, defaults,
             defaults to 'crud' (create read update delete)
        check_fields (list): the list of fields to check if they match
             the request's user. Defaults to 'self' and 'user'.
             Specify either the field that is a User, or specify
             'field.attribute' if it is a related field
        require_perm (bool|str): if True, will use DjangoAuthorization
             to verify django-level permission before checking self
             authorization (that is, the user must have both Django
             permission and the object must belong to them). If a
             string, will use user.has_perm() to check the same
    """

    def __init__(self, allow_staff=True, actions='crud', check_fields=None,
                 require_perm=False,
                 **kwargs):
        super().__init__(**kwargs)
        self.allow_staff = allow_staff
        self.actions = actions
        self.check_fields = check_fields or ('self', 'user',)
        self.require_perm = require_perm

    def is_superuser(self, bundle):
        valid = bundle.request.user.is_superuser
        valid |= (self.allow_staff and bundle.request.user.is_staff)
        return valid

    def is_active(self, bundle):
        return bundle.request.user.is_active

    def action_allowed(self, action, bundle):
        return action[0] in self.actions or self.is_superuser(bundle)

    def check_obj_perm(self, obj, bundle):
        # user must be owner of the object or superuser
        allowed = False
        request_user = bundle.request.user
        for field in self.check_fields:
            if not '.' in field:
                check_obj = obj if field == 'self' else getattr(obj, field, None)
            else:
                field, attribute = field.split('.')
                check_obj = getattr(getattr(obj, field), attribute)
            allowed |= (check_obj is not None and check_obj == request_user)
        allowed |= self.is_superuser(bundle)
        if allowed:
            return True
        return False

    def check_django_perm(self, scope, action, object_list, bundle):
        if isinstance(self.require_perm, str) and bundle.request.user.has_perm(self.require_perm):
            return True
        else:
            # loosely adopted from DjangoAuthorization
            perm_action_map = {
                'read': 'view',
                'update': 'change',
                'delete': 'delete',
                'create': 'add'
            }
            if scope == 'list':
                model = object_list.model
            else:
                model = bundle.obj.__class__
            perm_action = perm_action_map.get(action)
            permission = '{}.{}_{}'.format(model._meta.app_label, perm_action, get_module_name(model._meta))
            if bundle.request.user.has_perm(permission):
                return True
        raise Unauthorized("You are not allowed to access that resource.")

    def check_perm(self, scope, action, object_list, bundle):
        # reduce list of objects to those allowed for user
        if self.is_active(bundle):
            # check django permissions if requested
            if self.require_perm:
                self.check_django_perm(scope, action, object_list, bundle)
            # check object permissions
            objects_to_check = (object_list if scope == 'list' else [bundle.obj])
            filtered = [obj for obj in objects_to_check if self.check_obj_perm(obj, bundle)]
            if filtered:
                return filtered if scope == 'list' else True
        raise Unauthorized("You are not allowed to access that resource.")

    def check_list(self, object_list, bundle, action):
        if self.action_allowed(action, bundle):
            return object_list if self.check_perm('list', action, object_list, bundle) else []
        raise Unauthorized("You are not allowed to access that resource.")

    def create_list(self, object_list, bundle):
        return self.check_list(object_list, bundle, 'create')

    def read_list(self, object_list, bundle):
        return self.check_list(object_list, bundle, 'read')

    def update_list(self, object_list, bundle):
        return self.check_list(object_list, bundle, 'update')

    def delete_list(self, object_list, bundle):
        return self.check_list(object_list, bundle, 'delete')

    def create_detail(self, object_list, bundle):
        return self.action_allowed('create', bundle) and self.check_perm('detail', 'create', object_list, bundle)

    def read_detail(self, object_list, bundle):
        return self.action_allowed('read', bundle) and self.check_perm('detail', 'read', object_list, bundle)

    def update_detail(self, object_list, bundle):
        return self.action_allowed('update', bundle) and self.check_perm('detail', 'update', object_list, bundle)

    def delete_detail(self, object_list, bundle):
        return self.action_allowed('delete', bundle) and self.check_perm('detail', 'delete', object_list, bundle)
