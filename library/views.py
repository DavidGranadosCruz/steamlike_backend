import json

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import LibraryEntry


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


def error_validacion(details):
    return JsonResponse(
        {
            "error": "validation_error",
            "message": "Datos de entrada invalidos",
            "details": details,
        },
        status=400,
    )


def error_duplicado(details):
    return JsonResponse(
        {
            "error": "duplicate_entry",
            "message": "El juego ya existe en la biblioteca",
            "details": details,
        },
        status=400,
    )


def leer_json(request):
    if not request.body:
        return {}

    try:
        return json.loads(request.body)
    except Exception:
        return None


@csrf_exempt
@require_POST
def crear_entrada_biblioteca(request):
    data = leer_json(request)
    if data is None:
        return error_validacion({"body": "JSON mal formado."})

    if not isinstance(data, dict):
        return error_validacion({"body": "El JSON debe ser un objeto."})

    if data == {}:
        return error_validacion({"body": "El JSON no puede estar vacio."})

    details = {}

    if "external_game_id" not in data:
        details["external_game_id"] = "Campo obligatorio."
    elif not isinstance(data["external_game_id"], str):
        details["external_game_id"] = "Debe ser string."

    if "status" not in data:
        details["status"] = "Campo obligatorio."
    elif not isinstance(data["status"], str):
        details["status"] = "Debe ser string."
    elif data["status"] not in LibraryEntry.ALLOWED_STATUSES:
        details["status"] = "Debe ser uno de: wishlist, playing, completed, dropped."

    if "hours_played" not in data:
        details["hours_played"] = "Campo obligatorio."
    elif isinstance(data["hours_played"], bool) or not isinstance(data["hours_played"], int):
        details["hours_played"] = "Debe ser integer."
    elif data["hours_played"] < 0:
        details["hours_played"] = "Debe ser mayor o igual que 0."

    if details:
        return error_validacion(details)

    try:
        with transaction.atomic():
            entrada = LibraryEntry.objects.create(
                external_game_id=data["external_game_id"],
                status=data["status"],
                hours_played=data["hours_played"],
            )
    except IntegrityError:
        return error_duplicado(
            {"external_game_id": "duplicate"}
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
