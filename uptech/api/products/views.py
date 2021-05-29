from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from contrib.drf.viewsets import BaseViewSet
from uptech.api.products.serializers import ProductSerializer
from uptech.product.models import Product


class ProductFilterSet(filters.FilterSet):
    name = filters.CharFilter(method="filter_by_name")

    class Meta:
        model = Product
        fields = ["name"]

    def filter_by_name(self, queryset, name, value):
        assert name == "name"
        return queryset.filter(name__istartswith=value)


@extend_schema(tags=["products"])
class ProductsViewSet(BaseViewSet):
    filterset_class = None

    serializer_class_map = {
        "search": ProductSerializer,
    }

    ordering = "id"

    def get_queryset(self):
        return Product.objects.all()

    @extend_schema(responses=ProductSerializer(many=True))
    @action(
        ["get"],
        detail=False,
        filter_backends=[filters.DjangoFilterBackend],
        filterset_class=ProductFilterSet,
        permission_classes=[AllowAny],
    )
    def search(self, request):
        return self._list()
