from decimal import Decimal
from typing import List

from rest_framework import serializers
from rest_framework.serializers import ListSerializer

from contrib.drf.serializers import ModelSerializer, Serializer
from uptech.product.models import Product


class ProductListSerializer(ListSerializer):
    def to_representation(self, data: List[Product]):
        analogues = Product.objects.in_bulk([a_id for item in data for a_id in item.analogue_ids])
        for item in data:
            item._analogues = [analogues[a_id] for a_id in item.analogue_ids]

        return super().to_representation(data)


class InnerProductSerializer(ModelSerializer):

    is_effective = serializers.BooleanField(read_only=True)
    is_cheapest = serializers.BooleanField(read_only=True)
    is_trustworthy = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = read_only_fields = [
            "id",
            "sber_product_id",
            "name",
            "country",
            "dosage",
            "drug_form",
            "form_name",
            "is_recipe",
            "manufacturer",
            "packing",
            "price",
            "detail_page_url",
            "analogue_ids",
            "medsis_id",
            "effectiveness",
            "safety",
            "convenience",
            "contraindications",
            "side_effects",
            "tolerance",
            "score",
            "is_effective",
            "is_cheapest",
            "is_trustworthy",
        ]


class AnalogueProductSerializer(InnerProductSerializer):
    is_effective = serializers.BooleanField(read_only=True, source="_is_effective")
    is_cheapest = serializers.BooleanField(read_only=True, source="_is_cheapest")
    is_trustworthy = serializers.BooleanField(read_only=True, source="_is_trustworthy")


class ProductSerializer(InnerProductSerializer):
    analogues = AnalogueProductSerializer(read_only=True, many=True, source="_analogues")

    class Meta(InnerProductSerializer.Meta):
        list_serializer_class = ProductListSerializer
        fields = read_only_fields = InnerProductSerializer.Meta.fields + [
            "analogues",
        ]

    def to_representation(self, obj: Product) -> dict:
        if not hasattr(obj, "_analogues"):
            obj._analogues = [*Product.objects.filter(pk__in=obj.analogue_ids)]

        cheapest_analogue_ids = obj.get_cheaper_analogue_ids()
        for a in obj._analogues:
            a._is_cheapest = a.pk in cheapest_analogue_ids
            a._is_trustworthy = a.trustworthy_rate > obj.trustworthy_rate

            a._is_effective = False
            if a.effectiveness:
                a._is_effective = not obj.effectiveness or a.effectiveness > obj.effectiveness

        return super().to_representation(obj)


class ProductInfoSerializer(Serializer):
    cheapest = ProductSerializer(read_only=True)
    effective = ProductSerializer(read_only=True)

    def to_representation(self, obj: Product) -> dict:
        analogues = [*Product.objects.filter(pk__in=obj.analogue_ids, medsis_id__isnull=False, price__isnull=False)]
        if not analogues:
            return {"cheapest": None, "effective": None}

        sorted_by_price = sorted(analogues, key=lambda item: item.price)
        for p in sorted_by_price:
            if p.score >= Decimal("6"):
                cheapest = p
                break
        else:
            cheapest = sorted_by_price[0] if sorted_by_price else None

        sorted_by_effectiveness = sorted(analogues, key=lambda item: -item.effectiveness)
        for p in sorted_by_effectiveness:
            if p.score >= Decimal("6") and p.effectiveness >= 80:
                effective = p
                break
        else:
            effective = sorted_by_effectiveness[0] if sorted_by_effectiveness else None

        return super().to_representation({"cheapest": cheapest, "effective": effective})
