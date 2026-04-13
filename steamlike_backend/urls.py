from django.contrib import admin
from django.urls import include, path

from library.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/library/", include("library.urls")),
]