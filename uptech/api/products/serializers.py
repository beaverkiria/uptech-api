from decimal import Decimal

from contrib.drf.serializers import ModelSerializer, Serializer
from uptech.product.models import Product


class ProductSerializer(ModelSerializer):
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
        ]


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
