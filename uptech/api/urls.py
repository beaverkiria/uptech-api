from django.urls import include, path
from rest_framework.routers import DefaultRouter

from uptech.api.products.views import ProductsViewSet

router = DefaultRouter()

router.register(r"v1/products", ProductsViewSet, basename="products")

urlpatterns = [
    path("", include(router.urls)),
]
