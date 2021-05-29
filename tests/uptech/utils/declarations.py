from typing import Dict, Type

import factory
from factory.declarations import SKIP, BaseDeclaration
from factory.errors import InvalidDeclarationError


class _ItemFactory(BaseDeclaration):
    def __init__(self, idx: int, count_attr: str, factory_cls: Type[factory.Factory], context: Dict):
        super().__init__()
        self.idx = idx
        self.count_attr = count_attr
        self.factory = factory.SubFactory(factory_cls, **context)

    def evaluate(self, instance, step, extra):
        item_count = getattr(instance, self.count_attr)
        if item_count > self.idx:
            return self.factory.evaluate(instance=instance, step=step, extra=extra)
        if extra:
            raise InvalidDeclarationError(
                f"Received context for unused item {self.idx} ({self.count_attr} is {item_count})"
            )
        return SKIP

    def __repr__(self):
        return f"_ItemFactory({self.idx!r}, {self.count_attr!r}, {self.factory.factory_wrapper.get()!r})"


class _ParamsWithMeta(type):
    attr_name: str
    factory_cls: Type[factory.Factory]
    context: Dict = {}

    def __new__(mcs, name, bases, attrs):
        if not attrs.get("_skip"):
            attr_name = mcs.attr_name
            count_attr = f"{attr_name}_count"
            attrs.setdefault(count_attr, 0)
            for idx in range(10):
                attrs.setdefault(f"{attr_name}_{idx}", _ItemFactory(idx, count_attr, mcs.factory_cls, mcs.context))
        return super().__new__(mcs, name, bases, attrs)


class AttrList(BaseDeclaration):
    """
    Allow to build list by extending Params meta class of factory.

    You have tp provide base param attribute name (param_attr_name). It will be used to build parameters:
    * {param_attr_name}_count - number of elements in list
    * {param_attr_name}_0, {param_attr_name}_1, ..., {param_attr_name}_9 - elements in this list

    Also you have to provider factory for item creation.
    Additionally, you can provide a context for items as kwarg arguments.

    As a final step you must use attr.params as a base for Params metaclass

        class ExampleFactory(FactoryWithClean):
            items = AttrList("item", ItemFactory, foo=factory.SelfAttribute(".context_var")

            class Meta:
                model = ExampleModel

            class Params(items.params):
                context_var = factory.SubFactory(OtherFactory)

    You can't create more than 10 elements with context.
    """

    def __init__(self, param_attr_name: str, factory_cls: Type[factory.Factory], **kwarg):
        super().__init__()
        self.attr_name = param_attr_name
        self.count_attr = f"{self.attr_name}_count"
        self.factory_cls = factory_cls
        self.context = kwarg

    def evaluate(self, instance, step, extra):
        item_count = getattr(instance, self.count_attr)
        if item_count <= 0:
            return []

        result = [getattr(instance, f"{self.attr_name}_{idx}") for idx in range(min(item_count, 10))]
        assert item_count < 10 or not self.context, f"Can't create more that 10 {self.attr_name} with context"
        result += [self.factory_cls() for _ in range(10, item_count)]
        return result

    @property
    def params(self):
        meta_cls = type(
            "ItemMeta",
            (_ParamsWithMeta,),
            {"attr_name": self.attr_name, "factory_cls": self.factory_cls, "context": self.context},
        )
        return meta_cls("ItemParams", (), {"_skip": True})
