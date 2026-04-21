from django.contrib import admin
from django.urls import include, path

from library.views import health, registrar_usuario, iniciar_sesion, usuario_actual, cambiar_contraseña, cerrar_sesion

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/library/", include("library.urls")),
    path("api/auth/register/", registrar_usuario),
    path("api/auth/login/", iniciar_sesion),
    path("api/auth/logout/", cerrar_sesion),
    path("api/users/me/", usuario_actual),
    path("api/users/me/password/", cambiar_contraseña),
]