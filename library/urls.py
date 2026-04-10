from django.urls import path

from .views import entrada_biblioteca_detalle, entradas_biblioteca

urlpatterns = [
    path("entries/", entradas_biblioteca, name="entradas_biblioteca"),
    path("entries/<int:entry_id>/", entrada_biblioteca_detalle, name="entrada_biblioteca_detalle"),
]
