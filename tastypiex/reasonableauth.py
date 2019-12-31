from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized


class ReasonableDjangoAuthorization(DjangoAuthorization):
    """
    this implements a reasonable default for read operations

    this is a backwards compatible implementation of DjangoAuthorization
    in tastypie>=0.13.2 v.s. any previous version. See method read_perm_check
    for details.

    Usage:
        in a tastypie ModelResource add to Meta:

        authorization=ReasonableDjangoAuthorization()

        This will use the default add, change, delete object permissions
        to decide the object list for any PUT/PATCH/DELETE requests. It will
        use the view permission for any GET request (if the view permission
        exists on the model), or allow any GET request (if the view permission
        does not exists).

        Since the view permission is not yet a standard Django permission,
        you may change the actual permission:

        authorization=ReasonableDjangoAuthorization(read_permission='view')

    Motivation:
        Unfortunately the new tastypie maintainer has decided to implement
        a mind-blowingly ignorant default for read requests, which is to
        require the _change_ permission. We're reverting that and require
        the _view_ permission instead, which is in-line with an upcoming
        addition to Django.

    Details see
    https://github.com/django-tastypie/django-tastypie/issues/1407#issuecomment-201374930
    https://github.com/django/django/pull/5297
    """

    def __init__(self, read_permission='view'):
        super(ReasonableDjangoAuthorization, self).__init__()
        self._permission_exists = {}
        self.READ_PERM_CODE = read_permission

    def check_permission_exists(self, perm, model):
        """
        cached test for existence of a permission

        this tests if the permission exists on the model or model
        class. it then sets the view_permission_exists property which
        serves as a cache on subsequent calls. this works because
        an Authorization instance is always bound to one single tastypie
        resource, so it is safe to assume we're always asked for the same
        model / class.
        """
        if self._permission_exists.get(perm) is not None:
            return self._permission_exists[perm]
        try:
            content_type = ContentType.objects.get_for_model(model)
            Permission.objects.get(content_type=content_type, codename=perm)
        except:
            self._permission_exists[perm] = False
        else:
            self._permission_exists[perm] = True
        return self._permission_exists.get(perm)

    def read_detail(self, object_list, bundle):
        """
        check for read permission

        if the 'view' permission exists for the model, will check it.
        if no 'view' permission exists will default to true for any GET
        request, and require the change permission for any PUT or PATCH
        request.
        """
        if self.check_permission_exists(self.READ_PERM_CODE, bundle.obj):
            # 'view' permission exist, behavior is implemented in parent class
            return super(ReasonableDjangoAuthorization, self).read_detail(object_list, bundle)
        # 'view' permission does not exists, depend on request
        if bundle.request.method == 'GET':
            return True
        if bundle.request.method in ['PUT', 'PATCH']:
            return self.perm_obj_checks(bundle.request,
                                        'change', bundle.obj)
        if bundle.request.method in ['DELETE']:
            return self.perm_obj_checks(bundle.request,
                                        'delete', bundle.obj)
        raise Unauthorized("You are not allowed to access that resource.")

    def read_list(self, object_list, bundle):
        if self.check_permission_exists(self.READ_PERM_CODE, object_list):
            # 'view' permission exist, behavior is implemented in parent class
            return super(ReasonableDjangoAuthorization, self).read_detail(object_list, bundle)
        # 'view' permission does not exists, depend on request
        if bundle.request.method == 'GET':
            return object_list
        if bundle.request.method in ['PUT', 'PATCH']:
            return self.perm_list_checks(bundle.request,
                                         'change', object_list)
        if bundle.request.method in ['DELETE']:
            return self.perm_obj_checks(bundle.request,
                                        'delete', object_list)
        return object_list.none()

