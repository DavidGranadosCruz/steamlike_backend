from django.urls import path

from .views import detalle_entrada_biblioteca, entradas_biblioteca

urlpatterns = [
    path("entries/", entradas_biblioteca, name="entradas_biblioteca"),
    path("entries/<int:entry_id>/", detalle_entrada_biblioteca, name="detalle_entrada_biblioteca"),
]
