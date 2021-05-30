import pytest
from django.urls import reverse

from uptech.product.models import Product

pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture()
def url():
    def wrap(pk):
        return reverse("api:products-info", args=(pk,))

    return wrap


def test_no_analogues(client, url):
    p1 = Product.objects.create(sber_product_id=1, name="AbAcA")

    resp = client.get(url(p1.pk), format="json")
    assert resp.data == {"effective": None, "cheapest": None}


def test_info(client, url):
    p1 = Product.objects.create(
        sber_product_id=1,
        name="AbAcA",
        price=10,
        score="5",
        medsis_id=1,
        effectiveness=1,
    )
    p2 = Product.objects.create(
        sber_product_id=2,
        name="AbAcA",
        price=11,
        score="7",
        medsis_id=2,
        effectiveness=1,
    )
    p3 = Product.objects.create(
        sber_product_id=3,
        name="AbAcA",
        price=12,
        score=8,
        medsis_id=3,
        effectiveness=80,
    )
    p = Product.objects.create(
        sber_product_id=4,
        name="AbAcA",
        analogue_ids=[p1.pk, p2.pk, p3.pk],
        effectiveness=1,
    )

    resp = client.get(url(p.pk), format="json")
    assert resp.data["cheapest"]["id"] == p2.pk
    assert resp.data["effective"]["id"] == p3.pk
