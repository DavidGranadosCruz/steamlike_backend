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


def _respuesta_error(mensaje: str) -> JsonResponse:
    return JsonResponse({"error": mensaje}, status=400)


@csrf_exempt
@require_POST
def crear_entrada_biblioteca(request):
    try:
        cuerpo = request.body.decode("utf-8") if request.body else ""
        datos = json.loads(cuerpo or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _respuesta_error("El cuerpo JSON no es valido.")

    if not isinstance(datos, dict):
        return _respuesta_error("El cuerpo JSON debe ser un objeto.")

    if datos == {}:
        return _respuesta_error("El cuerpo JSON no puede estar vacio.")

    campos_obligatorios = ("external_game_id", "status", "hours_played")
    campos_faltantes = [campo for campo in campos_obligatorios if campo not in datos]
    if campos_faltantes:
        return _respuesta_error(
            f"Faltan campos obligatorios: {', '.join(campos_faltantes)}"
        )

    external_game_id = datos.get("external_game_id")
    status = datos.get("status")
    hours_played = datos.get("hours_played")

    if not isinstance(external_game_id, str):
        return _respuesta_error("external_game_id debe ser un string.")

    if not isinstance(status, str):
        return _respuesta_error("status debe ser un string.")

    if status not in LibraryEntry.ALLOWED_STATUSES:
        return _respuesta_error(
            "status debe ser uno de estos valores: wishlist, playing, completed, dropped."
        )

    if isinstance(hours_played, bool) or not isinstance(hours_played, int):
        return _respuesta_error("hours_played debe ser un integer.")

    if hours_played < 0:
        return _respuesta_error("hours_played debe ser mayor o igual que 0.")

    try:
        entrada = LibraryEntry.objects.create(
            external_game_id=external_game_id,
            status=status,
            hours_played=hours_played,
        )
    except IntegrityError:
        return _respuesta_error(
            "Ya existe una entrada de biblioteca con ese external_game_id."
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
