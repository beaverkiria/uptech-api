import pytest
from pytest_django.lazy_django import skip_if_no_django
from rest_framework.test import APIClient


@pytest.fixture()
def client():
    """A Django test client instance."""
    skip_if_no_django()

    return APIClient()
