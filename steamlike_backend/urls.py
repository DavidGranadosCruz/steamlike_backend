from django.contrib import admin
from django.urls import include, path

from library.views import health, register_user, login_user, me_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/library/", include("library.urls")),
    path("api/auth/register/", register_user),
    path("api/auth/login/", login_user),
    path("api/users/me/", me_view),
]