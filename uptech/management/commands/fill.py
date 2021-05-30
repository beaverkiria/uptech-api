import json
import os
from collections import defaultdict

from django.core.management import BaseCommand

from django.conf import settings

from uptech.product.models import Product
from uptech.utils import chunks


class Command(BaseCommand):

    PROPERTY_NAME_OVERRIDES = {}
    PRODUCTS_LIMIT = 100000

    def add_arguments(self, parser):
        parser.add_argument(
            "--products", action="store_true", help="Fill product database"
        )
        parser.add_argument(
            "--basket", action="store_true", help="Fill basket in database"
        )
        parser.add_argument("--medsis", action="store_true", help="Fill medsis data")

    def fill_products(self):
        products_data = {}
        with open(
            os.path.join(settings.BASE_DIR, "HackData", "products.json"), "r"
        ) as f:
            for p in json.load(f):
                products_data[p["ID"]] = {"sber_product_id": p["ID"], "name": p["NAME"]}

        print(f"Number of products: {len(products_data)}")

        model_fields = {f.name: f for f in Product._meta.get_fields()}
        print(f"DB product fields: {model_fields.keys()}")

        with open(
            os.path.join(settings.BASE_DIR, "HackData", "property.json"), "r"
        ) as f:
            properties = [
                p
                for p in json.load(f)
                if self.PROPERTY_NAME_OVERRIDES.get(p["ID"], p["CODE"].lower())
                in model_fields
            ]
        properties_data = {
            p["ID"]: self.PROPERTY_NAME_OVERRIDES.get(p["ID"], p["CODE"].lower())
            for p in properties
        }
        print(f"Properties to parse: {properties_data}")

        with open(
            os.path.join(settings.BASE_DIR, "HackData", "propertyValues.json"), "r"
        ) as f:
            values = json.load(f)

        for v in values:
            product_id = v["IBLOCK_ELEMENT_ID"]
            assert product_id and isinstance(
                product_id, int
            ), f"Invalid product id: {product_id}"
            for field_name, field_value in v.items():
                if not field_name.startswith("PROPERTY_"):
                    continue
                prop_id = int(field_name.split("_")[1])
                if prop_id not in properties_data:
                    continue
                products_data[product_id][properties_data[prop_id]] = field_value

        products_to_create = []
        products_to_update = Product.objects.in_bulk(
            products_data.keys(), field_name="sber_product_id"
        )
        for product_id, data in products_data.items():
            if product_id in products_to_update:
                for field_name, field_value in data.items():
                    setattr(products_to_update[product_id], field_name, field_value)
            else:
                products_to_create.append(Product(**data))

        if len(products_to_create) + len(products_to_update) > self.PRODUCTS_LIMIT:
            products_to_create = products_to_create[
                : self.PRODUCTS_LIMIT - len(products_to_update)
            ]

        print(f"Number of products to create: {len(products_to_create)}")

        print(f"Number of products to update: {len(products_to_update)}")

        Product.objects.bulk_create(products_to_create)
        Product.objects.bulk_update(
            products_to_update.values(),
            fields={*model_fields.keys()} - {"id", "sber_product_id"},
        )

    def fill_basket(self):
        with open(os.path.join(settings.BASE_DIR, "HackData", "basket.json"), "r") as f:
            data = json.load(f)

        products_map = Product.objects.in_bulk(
            [d["PRODUCT_ID"] for d in data], field_name="sber_product_id"
        )
        products_to_update = []
        for data_item in data:
            if data_item["PRODUCT_ID"] not in products_map:
                continue
            p = products_map[data_item["PRODUCT_ID"]]
            p.price = data_item["PRICE"]
            p.detail_page_url = data_item["DETAIL_PAGE_URL"]
            products_to_update.append(p)

        print(f"Number of products to update basket: {len(products_to_update)}")
        cnt = 0
        for p_chunk in chunks(products_to_update, 500):
            Product.objects.bulk_update(p_chunk, ["price", "detail_page_url"])
            cnt += p_chunk
            print(cnt)

    def fill_medsis(self):
        with open(
            os.path.join(settings.BASE_DIR, "HackData", "medsis_id_map.json"), "r"
        ) as f:
            sber_to_medsis = {
                item["sber_id"]: item["medsis_ids"][0]
                for item in json.load(f)
                if item["medsis_ids"]
            }
        medsis_to_sber = defaultdict(list)
        for sber_id, medsis_id in sber_to_medsis.items():
            medsis_to_sber[medsis_id].append(sber_id)

        with open(
            os.path.join(settings.BASE_DIR, "HackData", "parsed_drub_data.json"), "r"
        ) as f:
            data = {item["medsis_id"]: item for item in json.load(f)}

        product_map = Product.objects.in_bulk(
            sber_to_medsis.keys(), field_name="sber_product_id"
        )
        products_to_update = []
        for sber_id, p in product_map.items():
            if not sber_to_medsis.get(sber_id):
                continue

            medsis_id = sber_to_medsis[sber_id]

            p.medsis_id = medsis_id
            p.effectiveness = data[medsis_id]["effectiveness"]
            p.safety = data[medsis_id]["safety"]
            p.convenience = data[medsis_id]["convenience"]
            p.contraindications = data[medsis_id]["contraindications"]
            p.side_effects = data[medsis_id]["side_effects"]
            p.tolerance = data[medsis_id]["tolerance"]
            p.score = data[medsis_id]["score"]
            p.analogue_ids = [
                product_map[s_id].pk
                for m_id in data[medsis_id]["analogue_medsis_ids"]
                for s_id in medsis_to_sber[m_id]
                if s_id in product_map
            ]

            products_to_update.append(p)

        print(f"Number of products to update medsis: {len(products_to_update)}")
        cnt = 0
        for p_chunk in chunks(products_to_update, 500):
            Product.objects.bulk_update(
                p_chunk,
                [
                    "medsis_id",
                    "effectiveness",
                    "safety",
                    "convenience",
                    "contraindications",
                    "side_effects",
                    "tolerance",
                    "score",
                    "analogue_ids",
                ],
            )
            cnt += p_chunk
            print(cnt)

    def handle(self, *args, **options):
        if options["products"]:
            self.fill_products()
        if options["basket"]:
            self.fill_basket()
        if options["medsis"]:
            self.fill_medsis()
