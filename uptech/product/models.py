from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Product(models.Model):
    class Meta:
        db_table = "product"
        constraints = [
            models.UniqueConstraint(fields=["sber_product_id"], name="unique_sber_product_id"),
        ]
        indexes = [
            GinIndex(
                fields=["name"],
                name="name_gin_idx",
                fastupdate=False,
                opclasses=["gin_trgm_ops"],
            )
        ]

    sber_product_id = models.IntegerField()
    name = models.CharField(max_length=400)
    country = models.CharField(max_length=50, null=True)
    dosage = models.CharField(max_length=50, null=True)
    drug_form = models.CharField(max_length=100, null=True)
    form_name = models.CharField(max_length=100, null=True)
    is_recipe = models.BooleanField(default=False)
    manufacturer = models.CharField(max_length=300, null=True)
    packing = models.CharField(max_length=100, null=True)
