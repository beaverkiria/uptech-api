import pytest
from django.urls import reverse

from uptech.product.models import Product

pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture()
def url():
    def wrap(pk):
        return reverse("api:products-detail", args=(pk,))

    return wrap


def test_retrieve(client, url):
    p1 = Product.objects.create(
        sber_product_id=1,
        name="a",
        price=10,
        score="5",
        medsis_id=1,
        effectiveness=1,
        safety=10,
        side_effects=1,
        contraindications=1,
    )
    p2 = Product.objects.create(
        sber_product_id=2,
        name="b",
        price=11,
        score="7",
        medsis_id=2,
        effectiveness=1,
        safety=1,
        side_effects=1,
        contraindications=1,
    )
    p3 = Product.objects.create(
        sber_product_id=3,
        name="c",
        price=12,
        score=8,
        medsis_id=3,
        effectiveness=80,
        safety=1,
        side_effects=1,
        contraindications=1,
    )
    p = Product.objects.create(
        sber_product_id=4,
        name="d",
        analogue_ids=[p1.pk, p2.pk, p3.pk],
        effectiveness=1,
        score=9,
        price=1,
        medsis_id=4,
        safety=1,
        side_effects=1,
        contraindications=1,
    )

    resp = client.get(url(p.pk), format="json")
    assert resp.status_code == 200, resp.data
    assert resp.data["id"] == p.pk
    assert resp.data["is_cheapest"] is True
    assert resp.data["is_trustworthy"] is False
    assert resp.data["is_effective"] is False

    assert resp.data["analogues"][0]["id"] == p1.pk
    assert resp.data["analogues"][0]["is_cheapest"] is False
    assert resp.data["analogues"][0]["is_trustworthy"] is True
    assert resp.data["analogues"][0]["is_effective"] is False

    assert resp.data["analogues"][1]["id"] == p2.pk
    assert resp.data["analogues"][1]["is_cheapest"] is False
    assert resp.data["analogues"][1]["is_trustworthy"] is False
    assert resp.data["analogues"][1]["is_effective"] is False

    assert resp.data["analogues"][2]["id"] == p3.pk
    assert resp.data["analogues"][2]["is_cheapest"] is False
    assert resp.data["analogues"][2]["is_trustworthy"] is False
    assert resp.data["analogues"][2]["is_effective"] is True
