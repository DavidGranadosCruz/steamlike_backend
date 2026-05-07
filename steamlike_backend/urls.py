from django.contrib import admin
from django.urls import include, path, re_path

from steamlike_backend.views import frontend_app
from library.views import (
    buscar_catalogo,
    cambiar_contraseña,
    cerrar_sesion,
    debug_email_test,
    health,
    iniciar_sesion,
    registrar_usuario,
    resolver_catalogo,
    usuario_actual,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("api/health/", health),
    path("api/library/", include("library.urls")),
    path("api/auth/register/", registrar_usuario),
    path("api/auth/login/", iniciar_sesion),
    path("api/auth/logout/", cerrar_sesion),
    path("api/users/me/", usuario_actual),
    path("api/users/me/password/", cambiar_contraseña),
    path("api/catalog/search/", buscar_catalogo),
    path("api/catalog/resolve/", resolver_catalogo),
    path("api/debug/email/test/", debug_email_test),
    path("", frontend_app, name="frontend_app"),
    re_path(r"^(?!api/|admin/|static/).*$", frontend_app, name="frontend_app_spa"),
]
