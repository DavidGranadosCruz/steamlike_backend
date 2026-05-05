from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from library.views import health, registrar_usuario, iniciar_sesion, cerrar_sesion, usuario_actual, buscar_catalogo

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("api/health/", health),
    path("api/library/", include("library.urls")),
    path("api/auth/register/", registrar_usuario),
    path("api/auth/login/", iniciar_sesion),
    path("api/auth/logout/", cerrar_sesion),
    path("api/users/me/", usuario_actual),
    path("api/catalog/search/", buscar_catalogo),

    # Frontend — serve at root
    path("", TemplateView.as_view(template_name="index.html"), name="frontend"),
]
