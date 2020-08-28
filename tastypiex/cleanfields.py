"""
"""


class CleanBundleFieldsMixin(object):
    """
    Tastypie: remove any resource fields in a Resource's Meta

    fields
    excludes

    Tastypie's Resource does not process fields and excludes_fields
    as expected (that's a property of ModelResources). This mixin
    adds this capability

    The 'resource_uri' is never excluded, unless you set Meta.exclude_uri=True
    """

    def alter_detail_data_to_serialize(self, request, bundle):
        data = bundle.data
        if len(self._meta.fields or []):
            for k in [k for k in data.keys() if k not in self._meta.fields]:
                if k != 'resource_uri':
                    del data[k]
        for k in [k for k in data.keys() if k in self._meta.excludes]:
            del data[k]
        if getattr(self._meta, 'exclude_uri', False):
            del data['resource_uri']
        return data
