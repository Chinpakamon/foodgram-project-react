from rest_framework import mixins, viewsets


class ViewSetMixin(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    pass
