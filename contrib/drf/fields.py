import datetime

from drf_spectacular.utils import extend_schema_field
from rest_framework import fields, relations


@extend_schema_field(fields.IntegerField)
class TimestampField(fields.DateTimeField):
    def __init__(self, *args, **kwargs):
        kwargs["format"] = "%s"
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        dt = datetime.datetime.fromtimestamp(data)
        dt = self.enforce_timezone(dt)
        return dt

    def to_representation(self, value):
        str_timestamp = super().to_representation(value)
        return int(str_timestamp)


class QuerysetParentProxyPKRelatedField(relations.PrimaryKeyRelatedField):
    def get_queryset(self):
        assert callable(
            getattr(self.parent, "proxy_get_queryset", None)
        ), "Parent serializer has to have `proxy_get_queryset` method."
        return self.parent.proxy_get_queryset(self)
