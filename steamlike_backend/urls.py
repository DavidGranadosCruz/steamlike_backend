from django.contrib import admin
from django.urls import include, path

from library.views import health, registrar_usuario

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/library/", include("library.urls")),
    path("api/auth/register/", registrar_usuario),
]