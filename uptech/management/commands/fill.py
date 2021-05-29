import json
import os

from django.core.management import BaseCommand

from django.conf import settings

from uptech.product.models import Product


class Command(BaseCommand):

    PROPERTY_NAME_OVERRIDES = {}
    PRODUCTS_LIMIT = 5000

    def add_arguments(self, parser):
        parser.add_argument("--products", action="store_true", help="Fill product database")

    def fill_products(self):
        products_data = {}
        with open(os.path.join(settings.BASE_DIR, "HackData", "products.json"), "r") as f:
            for p in json.load(f):
                products_data[p["ID"]] = {"sber_product_id": p["ID"], "name": p["NAME"]}

        print(f"Number of products: {len(products_data)}")

        model_fields = {f.name: f for f in Product._meta.get_fields()}
        print(f"DB product fields: {model_fields.keys()}")

        with open(os.path.join(settings.BASE_DIR, "HackData", "property.json"), "r") as f:
            properties = [
                p for p in json.load(f) if self.PROPERTY_NAME_OVERRIDES.get(p["ID"], p["CODE"].lower()) in model_fields
            ]
        properties_data = {p["ID"]: self.PROPERTY_NAME_OVERRIDES.get(p["ID"], p["CODE"].lower()) for p in properties}
        print(f"Properties to parse: {properties_data}")

        with open(os.path.join(settings.BASE_DIR, "HackData", "propertyValues.json"), "r") as f:
            values = json.load(f)

        for v in values:
            product_id = v["IBLOCK_ELEMENT_ID"]
            assert product_id and isinstance(product_id, int), f"Invalid product id: {product_id}"
            for field_name, field_value in v.items():
                if not field_name.startswith("PROPERTY_"):
                    continue
                prop_id = int(field_name.split("_")[1])
                if prop_id not in properties_data:
                    continue
                products_data[product_id][properties_data[prop_id]] = field_value

        products_to_create = []
        products_to_update = Product.objects.in_bulk(products_data.keys(), field_name="sber_product_id")
        for product_id, data in products_data.items():
            if product_id in products_to_update:
                for field_name, field_value in data.items():
                    setattr(products_to_update[product_id], field_name, field_value)
            else:
                products_to_create.append(Product(**data))

        if len(products_to_create) + len(products_to_update) > self.PRODUCTS_LIMIT:
            products_to_create = products_to_create[: self.PRODUCTS_LIMIT - len(products_to_update)]

        print(f"Number of products to create: {len(products_to_create)}")
        print(f"Sber product ids to be created: {[p.sber_product_id for p in products_to_create]}")

        print(f"Number of products to update: {len(products_to_update)}")
        print(f"Sber product ids to be updated: {products_to_update.keys()}")

        Product.objects.bulk_create(products_to_create)
        Product.objects.bulk_update(
            products_to_update.values(),
            fields={*model_fields.keys()} - {"id", "sber_product_id"},
        )

    def handle(self, *args, **options):
        if options["products"]:
            self.fill_products()
