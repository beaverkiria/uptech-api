from contrib.drf.serializers import ModelSerializer
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
        ]
