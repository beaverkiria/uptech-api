from django.contrib.postgres.fields import ArrayField
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
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    detail_page_url = models.CharField(null=True, max_length=100)
    analogue_ids = ArrayField(models.BigIntegerField(), default=list)
    medsis_id = models.IntegerField(null=True)
    effectiveness = models.IntegerField(null=True)
    safety = models.IntegerField(null=True)
    convenience = models.IntegerField(null=True)
    contraindications = models.IntegerField(null=True)
    side_effects = models.IntegerField(null=True)
    tolerance = models.IntegerField(null=True)
    score = models.DecimalField(max_digits=3, decimal_places=1, null=True)

    def __str__(self):
        return f"Product(id={self.id}, sber_product_id={self.sber_product_id}, medsis_id={self.medsis_id}, name={self.name})"
