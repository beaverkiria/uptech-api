"""uptech URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from uptech.api import urls as api


def trigger_error(request):
    raise Exception("Error occured")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include((api, "api"), namespace="api")),
    path("sentry-debug/", trigger_error),
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    url(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
]

if settings.BACKEND_ENV in (settings.LOCAL, settings.STAGE):
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        # Optional UI:
        path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    ]
