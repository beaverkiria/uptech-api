# See https://gist.github.com/surenkov/8a5f1f6bf0b24ede162e1623de2b81d2

import logging
import typing as t
from contextlib import suppress
from functools import partial

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import JSONField
from django.db.models.query_utils import DeferredAttribute
from pydantic import BaseConfig, BaseModel, ValidationError
from pydantic.main import create_model
from pydantic.typing import display_as_type
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer

logger = logging.getLogger(__name__)

SchemaT = t.Union[None, BaseModel, t.Sequence[BaseModel], t.Mapping[str, BaseModel]]
ST = t.TypeVar("ST", bound=SchemaT)

ModelType = t.Type[BaseModel]
ConfigType = t.Type[BaseConfig]


def default_error_handler(obj, err):
    logger.error("Can't parse object with the schema: obj=%s, errors=%s", obj, err)
    return obj


def serializer_error_handler(obj, err):
    raise serializers.ValidationError(err[1])


class SchemaDeferredAttribute(DeferredAttribute):
    """
    Forces Django to call to_python on fields when setting them.
    This is useful when you want to add some custom field data postprocessing.

    Should be added to field like a so:

    ```
    def contribute_to_class(self, cls, name, *args, **kwargs):
        super().contribute_to_class(cls, name,  *args, **kwargs)
        setattr(cls, name, SchemaDeferredAttribute(self))
    ```
    """

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)


class SchemaEncoder(DjangoJSONEncoder):
    def __init__(self, *args, schema: ModelType, **kwargs):
        self.schema = schema
        super().__init__(*args, **kwargs)

    def encode(self, obj):
        try:
            if isinstance(obj, self.schema):
                data = obj.json()
            else:
                data = self.schema(__root__=obj).json()
        except ValidationError:
            # This flow used for expressions like .filter(data__contains={}).
            # We don't want that {} to be parsed as schema.
            data = super().encode(obj)

        return data


class SchemaDecoder(t.Generic[ST]):
    def __init__(self, schema: ModelType, error_handler=default_error_handler):
        self.schema = schema
        self.error_handler = error_handler

    def decode(self, obj: t.Any) -> ST:
        if obj is None:
            return None
        try:
            if isinstance(obj, str):
                result = self.schema.parse_raw(obj)
            elif isinstance(obj, self.schema):
                result = obj
            else:
                result = self.schema(__root__=obj)

            while hasattr(result, "__root__"):
                result = result.__root__
            return result
        except ValidationError as e:
            err = e.errors()
        except Exception as e:
            err = str(e)

        return self.error_handler(obj, (self.schema, err))


class SchemaWrapper(t.Generic[ST]):
    def _wrap_schema(self, schema: t.Type[ST], config: ConfigType = None, **kwargs) -> ModelType:
        type_name = self._get_field_schema_name(schema)
        params = self._get_field_schema_params(schema, config, **kwargs)
        return create_model(type_name, **params)

    def _get_field_schema_name(self, schema: t.Type[t.Any]) -> str:
        return f"FieldSchema[{display_as_type(schema)}]"

    def _get_field_schema_params(self, schema: t.Type[t.Any], config: ConfigType = None, **kwargs) -> dict:
        params: t.Dict[str, t.Any] = dict(kwargs, __root__=(t.Optional[schema], ...))

        if config is None:
            with suppress(AttributeError):
                config = schema.Config

        if config is not None:
            params.update(__config__=config)

        return params


class JSONSchemaField(SchemaWrapper[ST], JSONField):
    def __init__(self, schema: t.Type[ST], config: ConfigType = None, *args, error_handler=default_error_handler, **kw):
        super().__init__(*args, **kw)
        self.schema = schema
        self.config = config
        # field_schema = self._wrap_schema(schema, config)
        self.decoder = partial(SchemaDecoder, schema=self.schema, error_handler=error_handler)
        self.encoder = partial(SchemaEncoder, schema=self.schema)

    def __copy__(self):
        _, _, args, kwargs = self.deconstruct()
        return type(self)(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(JSONField, self).deconstruct()
        kwargs.update(schema=self.schema, config=self.config)
        return name, path, args, kwargs

    def to_python(self, value) -> SchemaT:
        return self.decoder().decode(value)

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super().contribute_to_class(cls, name, *args, **kwargs)
        setattr(cls, name, SchemaDeferredAttribute(self))


class JSONSchemaSerializerField(SchemaWrapper[ST], serializers.Field):
    def __init__(self, schema: t.Type[ST], config: ConfigType = None, *args, include=None, exclude=None, **kwargs):
        super().__init__(*args, **kwargs)

        # self.schema = field_schema = self._wrap_schema(schema, config)
        self.schema = schema
        self.decoder = SchemaDecoder(self.schema, serializer_error_handler)
        self.include = include
        self.exclude = exclude

    def to_internal_value(self, data) -> t.Optional[ST]:
        return self.decoder.decode(data)

    def to_representation(self, value):
        obj = self.schema(__root__=value)

        if (include := self.include) is not None:
            include = {"__root__": include}

        if (exclude := self.exclude) is not None:
            exclude = {"__root__": exclude}

        raw_obj = obj.dict(include=include, exclude=exclude)  # type: ignore
        return raw_obj["__root__"]


class JSONSchemaRenderer(SchemaWrapper[ST], JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context["response"]
        if response.exception:
            return super().render(data, accepted_media_type, renderer_context)

        schema_ctx = self.get_schema_attrs(renderer_context or {})
        try:
            json_str = self.render_data(data, schema_ctx)
        except ValidationError as e:
            json_str = e.json()
        except AttributeError:
            json_str = super().render(data, accepted_media_type, renderer_context)
        return json_str

    def get_schema_attrs(self, renderer_context: dict):
        return dict(
            include=renderer_context.get("include"),
            exclude=renderer_context.get("exclude"),
        )

    def render_data(self, data, schema_ctx) -> bytes:
        if (schema := self.get_render_schema()) is not None:
            data = schema(__root__=data)

        json_str = data.json(**schema_ctx)
        return json_str.encode()

    def get_render_schema(self):
        with suppress(AttributeError):
            return self.output_schema

        try:
            spec_type = t.get_args(self.__orig_class__)[0]  # type: ignore
            schema = self._wrap_schema(spec_type)
        except (AttributeError, IndexError):
            schema = None

        self.output_schema = schema
        return schema
