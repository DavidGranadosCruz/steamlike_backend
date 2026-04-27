from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from library.views import health, registrar_usuario, iniciar_sesion, usuario_actual

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/library/", include("library.urls")),
    path("api/auth/register/", registrar_usuario),
    path("api/auth/login/", iniciar_sesion),
    path("api/users/me/", usuario_actual),

    # Frontend — serve at root
    path("", TemplateView.as_view(template_name="index.html"), name="frontend"),
]