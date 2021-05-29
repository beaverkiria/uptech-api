import pytest
from django.urls import reverse

from uptech.product.models import Product

pytestmark = [
    pytest.mark.django_db,
]

url = reverse("api:products-search")


def test_search(client):
    p1 = Product.objects.create(sber_product_id=1, name="AbAcA")
    p2 = Product.objects.create(sber_product_id=2, name="abCC")

    resp = client.get(url, format="json")
    assert resp.status_code == 200, resp.data
    results = resp.json()["results"]
    assert len(results) == 2
    assert results[0]["id"] == p1.pk
    assert results[1]["id"] == p2.pk

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
