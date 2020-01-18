from tastypie.exceptions import BadRequest
from tastypie.fields import ApiField


class FromModelField(ApiField):
    """
    A Resource field that gets objects from Django models by URI

    Use this instead of a ToRelatedField if all you want is for the
    user to specify a related object, but not be able to create or otherwise
    query, modify, delete the related object.

    Usage:

        For example, you want the user to be able to create a new resource FooResource
        and set Foo.user to an existing user. Then just specify the FooResource as
        usual and add a field like this:

            user = FromModelField('user', model=User)

        Now the API can be used to create a new user, with the 'user' field being
        the URI to an existing user. The Resource will populate the 'user' field
        from the URI. On return, the same URI will be returned, so no data
        is ever exposed other then what the user already knows.

        If you want the user to be able to specify other URIs than the default
        resource/pk/ format, set model_fields. For example, to enable the API
        to specify the username instead of the user's pk, specify:

             user = FromModelField('user', model=User, model_fields=['username'])

        You can also enable multiple fields, e.g. model_fields=['pk', 'username'].

        FromModelField does not verify user permissions. If you need to verify
        user permissions, specify a callable as

            user = FromModelField('user', model=User, check_perm=check)

            def check(bundle, obj):
                # return True if ok or else raise Unauthorized()
                ...

        If you are using Django guardian, implement check() as follows:

            def check(bundle, obj):
                if bundle.user.has_perm('permission', obj):
                    return True
                raise Unauthorized()


    Alternative:

        One alternative with Tastypie is to create a seperate RelatedResource
        and use a ToField, with no authorization check. In this case be sure
        to never expose the RelatedResource on an actual Api URL. While equally
        possible, it adds a lot of overhead and code for little added value.

        FromModelField makes the intent explicit and is faster to implement.
    """

    def __init__(self, attribute=None, model=None, model_fields=None,
                 check_perm=False, **kwargs):
        super().__init__(attribute=attribute, **kwargs)
        self.model = model
        self.model_fields = model_fields or ('pk',)
        self.check_perm = check_perm

    def try_model_field(self, field, key):
        try:
            value = int(key) if field== 'pk' else str(key)
            for level in field.split('__'):
                value = self.model.objects.get(**{level: value})
        except:
            return False, None
        return True, value

    def hydrate(self, bundle):
        # return a direct model object
        uri = bundle.data.get(self.attribute)
        if uri is None and self.null:
            return None
        try:
            pk = uri.strip('/').split('/')[-1]
            for field in self.model_fields:
                worked, obj = self.try_model_field(field, pk)
                if worked:
                    break
        except:
            raise BadRequest('Cannot read data from {uri}'.format(**locals()))
        if self.check_perm:
            self.check_perm(bundle, obj)
        return obj

    def dehydrate(self, bundle, for_list=True):
        # by default return whatever was provided as input
        return getattr(bundle.obj, self.attribute, bundle.data.get(self.attribute))
