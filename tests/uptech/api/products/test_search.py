import pytest
from django.urls import reverse

from uptech.product.models import Product

pytestmark = [
    pytest.mark.django_db,
]

url = reverse("api:products-search")


def test_search(client):
    p1 = Product.objects.create(sber_product_id=1, name="AbAcA")
    p2 = Product.objects.create(sber_product_id=2, name="abCC", analogue_ids=[p1.pk])

    resp = client.get(url, format="json")
    assert resp.status_code == 200, resp.data
    results = resp.json()["results"]
    assert len(results) == 2
    assert results[0]["id"] == p1.pk
    assert results[1]["id"] == p2.pk
    assert results[1]["analogues"][0]["id"] == p1.pk

    resp = client.get(f"{url}?name=ab", format="json")
    assert resp.status_code == 200, resp.data
    results = resp.json()["results"]
    assert len(results) == 2
    assert results[0]["id"] == p1.pk
    assert results[1]["id"] == p2.pk

    resp = client.get(f"{url}?name=c", format="json")
    assert resp.status_code == 200, resp.data
    results = resp.json()["results"]
    assert len(results) == 0

    resp = client.get(f"{url}?name=Aba", format="json")
    assert resp.status_code == 200, resp.data
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == p1.pk


def test_info(client):
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

    resp = client.get(f"{url}?name=d", format="json")
    assert resp.status_code == 200, resp.data
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == p.pk
    assert results[0]["is_cheapest"] is True
    assert results[0]["is_trustworthy"] is False
    assert results[0]["is_effective"] is False

    assert results[0]["analogues"][0]["id"] == p1.pk
    assert results[0]["analogues"][0]["is_cheapest"] is False
    assert results[0]["analogues"][0]["is_trustworthy"] is True
    assert results[0]["analogues"][0]["is_effective"] is False

    assert results[0]["analogues"][1]["id"] == p2.pk
    assert results[0]["analogues"][1]["is_cheapest"] is False
    assert results[0]["analogues"][1]["is_trustworthy"] is False
    assert results[0]["analogues"][1]["is_effective"] is False

    assert results[0]["analogues"][2]["id"] == p3.pk
    assert results[0]["analogues"][2]["is_cheapest"] is False
    assert results[0]["analogues"][2]["is_trustworthy"] is False
    assert results[0]["analogues"][2]["is_effective"] is True
