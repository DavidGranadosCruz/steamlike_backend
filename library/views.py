from __future__ import annotations

import json

from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import LibraryEntry


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


def _respuesta_error_validacion(detalles: dict[str, str]) -> JsonResponse:
    return JsonResponse(
        {
            "error": "validation_error",
            "message": "Datos de entrada inválidos",
            "details": detalles,
        },
        status=400,
    )


def _respuesta_error_duplicado(detalles: dict[str, str]) -> JsonResponse:
    return JsonResponse(
        {
            "error": "duplicate_entry",
            "message": "Ya existe una entrada con esos datos únicos.",
            "details": detalles,
        },
        status=400,
    )


@csrf_exempt
@require_POST
def crear_entrada_biblioteca(request):
    try:
        cuerpo = request.body.decode("utf-8") if request.body else ""
        datos = json.loads(cuerpo or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _respuesta_error_validacion({"body": "JSON mal formado."})

    if not isinstance(datos, dict):
        return _respuesta_error_validacion({"body": "El JSON debe ser un objeto."})

    if datos == {}:
        return _respuesta_error_validacion({"body": "El JSON no puede estar vacío."})

    campos_obligatorios = ("external_game_id", "status", "hours_played")
    detalles_errores: dict[str, str] = {}
    for campo in campos_obligatorios:
        if campo not in datos:
            detalles_errores[campo] = "Campo obligatorio."

    external_game_id = datos.get("external_game_id")
    status = datos.get("status")
    hours_played = datos.get("hours_played")

    if "external_game_id" not in detalles_errores and not isinstance(
        external_game_id, str
    ):
        detalles_errores["external_game_id"] = "Debe ser string."

    if "status" not in detalles_errores:
        if not isinstance(status, str):
            detalles_errores["status"] = "Debe ser string."
        elif status not in LibraryEntry.ALLOWED_STATUSES:
            detalles_errores["status"] = (
                "Debe ser uno de: wishlist, playing, completed, dropped."
            )

    if "hours_played" not in detalles_errores:
        if isinstance(hours_played, bool) or not isinstance(hours_played, int):
            detalles_errores["hours_played"] = "Debe ser integer."
        elif hours_played < 0:
            detalles_errores["hours_played"] = "Debe ser mayor o igual que 0."

    if detalles_errores:
        return _respuesta_error_validacion(detalles_errores)

    try:
        entrada = LibraryEntry.objects.create(
            external_game_id=external_game_id,
            status=status,
            hours_played=hours_played,
        )
    except IntegrityError:
        return _respuesta_error_duplicado(
            {"external_game_id": "Ya existe una entrada con ese identificador."}
        )

    return JsonResponse(
        {
            "id": entrada.id,
            "external_game_id": entrada.external_game_id,
            "status": entrada.status,
            "hours_played": entrada.hours_played,
        },
        status=201,
    )
