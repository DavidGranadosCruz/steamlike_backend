from django.urls import path

from .views import crear_entrada_biblioteca

urlpatterns = [
    path("entries/", crear_entrada_biblioteca, name="crear_entrada_biblioteca"),
]
