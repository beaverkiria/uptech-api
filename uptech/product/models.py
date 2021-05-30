import bisect
from decimal import Decimal
from math import ceil
from typing import Set, Optional

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Product(models.Model):
    class Meta:
        db_table = "product"
        constraints = [
            models.UniqueConstraint(
                fields=["sber_product_id"], name="unique_sber_product_id"
            ),
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

    def _preload_analogues(self):
        if not hasattr(self, "_analogues"):
            self._analogues = [
                *Product.objects.filter(
                    pk__in=self.analogue_ids,
                    price__isnull=False,
                    medsis_id__isnull=False,
                )
            ]
        return self._analogues

    @property
    def is_effective(self) -> bool:
        return (
            self.score
            and self.score > Decimal("6")
            and self.effectiveness
            and self.effectiveness >= 80
        )

    @property
    def is_cheapest(self) -> bool:
        if not self.score or self.score < Decimal(6):
            return False

        self._preload_analogues()
        if not self._analogues:
            return False

        sorted_analogues = sorted([a.price for a in self._analogues if a.price])
        price_position = bisect.bisect_left(sorted_analogues, self.price)
        if price_position <= ceil(len(self._analogues) / 10.0 * 3):
            return True

        return False

    @property
    def trustworthy_rate(self) -> float:
        if not self.score:
            return 0.0
        return (
            self.safety + (100 - self.side_effects) + (100 - self.contraindications)
        ) / 3.0

    @property
    def is_trustworthy(self) -> bool:
        return self.score and self.score >= Decimal("6") and self.trustworthy_rate >= 80

    def get_cheaper_analogue_ids(self) -> Set[int]:
        if not self.price or self.score:
            return set()
        self._preload_analogues()
        analogues = [a for a in self._analogues if a.score and a.price]
        return {
            a.pk
            for a in analogues
            if (self.price - a.price) / self.price > (a.score - self.score) / a.score
        }

    @property
    def image_url(self) -> Optional[str]:
        if not self.detail_page_url:
            return None

        good_id = self.detail_page_url.strip("/").split("/")[-1][2:]
        return f"https://cdn.eapteka.ru/upload/offer_photo/{good_id[:3]}/{good_id[3:]}/resized/450_450_1.jpeg"
