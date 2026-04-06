from django.contrib import admin
from django.urls import path, include
from library.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    #path("api/library/", include("core.urls")),
    path("api/health/", health)
]
