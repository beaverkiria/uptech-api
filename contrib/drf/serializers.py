from django.db import models
from rest_framework import serializers

from contrib.drf.fields import TimestampField


class CustomResponseSerializerMixin:
    def to_representation(self, obj) -> dict:
        if not hasattr(self, "Meta") or not hasattr(self.Meta, "response_serializer_class"):
            return super().to_representation(obj)
        response_serializer = self.Meta.response_serializer_class(self.context)
        return response_serializer.to_representation(obj)


class Serializer(CustomResponseSerializerMixin, serializers.Serializer):
    pass


class ModelSerializer(CustomResponseSerializerMixin, serializers.ModelSerializer):
    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.DateTimeField: TimestampField,
    }
