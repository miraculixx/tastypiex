class RequestFilteredQueryset:
    def get_object_list(self, request):
        qs = super().get_object_list(request)
        qs = qs.for_request(request) if hasattr(qs, 'for_request') else qs
        return qs
