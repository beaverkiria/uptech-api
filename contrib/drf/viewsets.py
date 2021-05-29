import typing

from rest_framework import permissions, response, serializers, status, viewsets
from rest_framework.generics import get_object_or_404


class BaseViewSet(viewsets.GenericViewSet):

    serializer_class_map: typing.Dict[str, typing.Type[serializers.Serializer]]
    serializer: serializers.Serializer
    ordering: str
    permission_classes_map: typing.Dict[str, typing.List[typing.Type[permissions.BasePermission]]]

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly." % (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_serializer_class(self) -> typing.Type[serializers.Serializer]:
        return self.serializer_class_map[self.action]

    def get_permissions(self):
        if hasattr(self, "permission_classes_map"):
            return [permission() for permission in self.permission_classes_map[self.action]]
        return super().get_permissions()

    def _create(self, success_status=status.HTTP_201_CREATED) -> response.Response:
        self.serializer = self.get_serializer(data=self.request.data)
        self.serializer.is_valid(raise_exception=True)
        self.serializer.save()
        return response.Response(self.serializer.data, status=success_status)

    def _retrieve(self, obj=None) -> response.Response:
        instance = obj or self.get_object()
        self.serializer = self.get_serializer(instance)
        return response.Response(self.serializer.data)

    def _list(self):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            self.serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(self.serializer.data)

        self.serializer = self.get_serializer(queryset, many=True)
        return response.Response(self.serializer.data)
